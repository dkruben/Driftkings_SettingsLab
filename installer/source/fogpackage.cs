// Optional map override. Reads original packages; never writes to res/packages.
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.IO.Compression;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text;
using System.Text.RegularExpressions;
using System.Xml;

internal static class FogPackage
{
    internal const string FileName = "Driftkings.RemoveFog.wotmod";
    internal const string ModId = "driftkings.removefog";
    static void Require(bool value, string reason) { if (!value) throw new InvalidDataException(reason); }
    static byte[] Slice(byte[] data, int start, int length) {
        Require(start >= 0 && length >= 0 && start <= data.Length - length, "Packed XML bounds");
        byte[] result = new byte[length]; Buffer.BlockCopy(data, start, result, 0, length); return result;
    }
    // PackedSection: uint16 child count, typed uint32 offsets, uint16 string indices.
    // Preserve all unknown values/types and rewrite only the requested fog leaves.
    static byte[] Section(byte[] data, int start, int length, List<string> names, string path, int depth, ref int changes) {
        Require(depth < 64 && length >= 6, "Invalid packed XML section");
        int count = BitConverter.ToUInt16(data, start), header = 6 + count * 6;
        Require(header <= length, "Truncated packed XML header");
        uint first = BitConverter.ToUInt32(data, start + 2);
        int previous = (int)(first & 0x0fffffff), payload = start + header;
        Require(previous <= length - header, "Invalid packed XML value");
        var body = new MemoryStream(); body.Write(data, payload, previous);
        var records = new List<KeyValuePair<ushort, uint>>();
        for (int i = 0; i < count; ++i) {
            int record = start + 6 + i * 6;
            ushort key = BitConverter.ToUInt16(data, record);
            uint descriptor = BitConverter.ToUInt32(data, record + 2), type = descriptor >> 28;
            int end = (int)(descriptor & 0x0fffffff);
            Require(key < names.Count && end >= previous && end <= length - header, "Invalid packed XML child");
            string childPath = path.Length == 0 ? names[key] : path + "/" + names[key];
            byte[] value = Slice(data, payload + previous, end - previous), replacement = value;
            if (type == 0) replacement = Section(data, payload + previous, end - previous, names, childPath, depth + 1, ref changes);
            else if (childPath == "Fog/enable" || childPath == "VolumetricFog/enabled" || childPath == "VolumetricFog/enableGameplay") {
                Require(type == 4 && (value.Length == 0 || (value.Length == 1 && value[0] == 1)), "Unexpected fog boolean format");
                replacement = new byte[0];
            } else if (childPath == "Fog/deferred/density" || childPath == "Fog/simplifiedDeferred/density" || childPath == "Fog/forward/density") {
                Require(type == 3 && value.Length == 4, "Unexpected fog density format"); replacement = new byte[4];
            }
            if (!Equal(value, replacement)) changes++;
            body.Write(replacement, 0, replacement.Length);
            records.Add(new KeyValuePair<ushort, uint>(key, ((uint)body.Length) | (type << 28)));
            previous = end;
        }
        Require(previous == length - header, "Trailing packed XML data");
        using (var result = new MemoryStream()) using (var writer = new BinaryWriter(result)) {
            writer.Write((ushort)count); writer.Write(first);
            foreach (var record in records) { writer.Write(record.Key); writer.Write(record.Value); }
            writer.Write(body.ToArray()); return result.ToArray();
        }
    }
    internal static bool Equal(byte[] left, byte[] right) {
        if (left.Length != right.Length) return false;
        for (int i = 0; i < left.Length; ++i) if (left[i] != right[i]) return false;
        return true;
    }
    internal static byte[] Patch(byte[] data) {
        Require(data.Length >= 12 && data.Length <= 2 * 1024 * 1024, "Environment size exceeds limit");
        Require(BitConverter.ToUInt32(data, 0) == 0x62a14e45 && data[4] == 0, "Unsupported environment format");
        int offset = 5; var names = new List<string>(); var utf8 = new UTF8Encoding(false, true);
        while (true) {
            int end = Array.IndexOf(data, (byte)0, offset);
            Require(end >= offset, "Invalid packed XML string table");
            if (end == offset) { offset++; break; }
            names.Add(utf8.GetString(data, offset, end - offset)); offset = end + 1;
        }
        int changes = 0;
        byte[] section = Section(data, offset, data.Length - offset, names, "", 0, ref changes);
        using (var output = new MemoryStream()) {
            output.Write(data, 0, offset); output.Write(section, 0, section.Length); return output.ToArray();
        }
    }
    internal static SortedDictionary<string, byte[]> Environments(string packages) {
        var result = new SortedDictionary<string, byte[]>(StringComparer.Ordinal);
        string[] files = Directory.GetFiles(packages, "*.pkg"); Array.Sort(files, StringComparer.Ordinal);
        foreach (string file in files) {
            if (!Regex.IsMatch(Path.GetFileName(file), @"^\d+_.+\.pkg$", RegexOptions.CultureInvariant) || file.EndsWith("_hd.pkg", StringComparison.OrdinalIgnoreCase)) continue;
            Safe(file);
            using (var stream = File.Open(file, FileMode.Open, FileAccess.Read, FileShare.Read))
            using (var zip = new ZipArchive(stream, ZipArchiveMode.Read)) {
                foreach (var entry in zip.Entries) {
                    if (!Regex.IsMatch(entry.FullName, @"\Aspaces/[A-Za-z0-9_-]+/environments/[A-Za-z0-9_-]+/environment\.xml\z")) continue;
                    Require(entry.Length > 0 && entry.Length <= 2 * 1024 * 1024 && result.Count < 4096, "Environment inventory limit");
                    byte[] data;
                    using (var input = entry.Open()) using (var output = new MemoryStream()) { input.CopyTo(output); data = output.ToArray(); }
                    byte[] previous;
                    if (result.TryGetValue(entry.FullName, out previous)) Require(Equal(previous, data), "Conflicting environment resources: " + entry.FullName);
                    else result.Add(entry.FullName, data);
                }
            }
        }
        Require(result.Count > 0, "No map environments found"); return result;
    }
    // Explicit stored ZIP writer: ZipArchive NoCompression can still select method 8.
    static uint Crc(byte[] data) {
        uint crc = 0xffffffff;
        foreach (byte value in data) { crc ^= value; for (int i = 0; i < 8; i++) crc = (crc >> 1) ^ ((crc & 1) != 0 ? 0xedb88320u : 0); }
        return crc ^ 0xffffffff;
    }
    internal static string SourceStamp(string packages) {
        string[] files = Directory.GetFiles(packages, "*.pkg"); Array.Sort(files, StringComparer.Ordinal);
        var text = new StringBuilder();
        foreach (string file in files) {
            string name = Path.GetFileName(file);
            if (!Regex.IsMatch(name, @"^\d+_.+\.pkg$", RegexOptions.CultureInvariant) || name.EndsWith("_hd.pkg", StringComparison.OrdinalIgnoreCase)) continue;
            Safe(file); var info = new FileInfo(file);
            long seconds = (info.LastWriteTimeUtc.Ticks - 621355968000000000L) / 10000000L;
            text.Append(name).Append(':').Append(info.Length).Append(':').Append(seconds).Append('\n');
        }
        using (var hash = SHA256.Create()) return BitConverter.ToString(hash.ComputeHash(Encoding.UTF8.GetBytes(text.ToString()))).Replace("-", "").ToLowerInvariant();
    }
    internal static int Build(string packages, string output) {
        string stamp = SourceStamp(packages);
        var entries = new SortedDictionary<string, byte[]>(StringComparer.Ordinal);
        int count = 0;
        foreach (var item in Environments(packages)) {
            byte[] patched = Patch(item.Value);
            if (!Equal(item.Value, patched)) { entries.Add("res/" + item.Key, patched); count++; }
        }
        Require(count > 0, "No fog values changed; package was not generated");
        Require(stamp == SourceStamp(packages), "Map packages changed during generation");
        entries.Add("meta.xml", Encoding.UTF8.GetBytes("<root><id>" + ModId + "</id><name>Driftkings Remove Fog</name><version>1.0.0</version><sources>" + stamp + "</sources><description>Generated from this client</description></root>"));
        using (var stream = new FileStream(output, FileMode.CreateNew, FileAccess.Write, FileShare.None))
        using (var writer = new BinaryWriter(stream)) {
            var central = new List<byte[]>();
            foreach (var item in entries) {
                byte[] name = Encoding.UTF8.GetBytes(item.Key), data = item.Value; uint crc = Crc(data), offset = (uint)stream.Position;
                writer.Write(0x04034b50u); writer.Write((ushort)20); writer.Write((ushort)0x800); writer.Write((ushort)0); writer.Write((ushort)0); writer.Write((ushort)33);
                writer.Write(crc); writer.Write((uint)data.Length); writer.Write((uint)data.Length); writer.Write((ushort)name.Length); writer.Write((ushort)0); writer.Write(name); writer.Write(data);
                using (var record = new MemoryStream()) using (var cw = new BinaryWriter(record)) {
                    cw.Write(0x02014b50u); cw.Write((ushort)20); cw.Write((ushort)20); cw.Write((ushort)0x800); cw.Write((ushort)0); cw.Write((ushort)0); cw.Write((ushort)33);
                    cw.Write(crc); cw.Write((uint)data.Length); cw.Write((uint)data.Length); cw.Write((ushort)name.Length); cw.Write((ushort)0); cw.Write((ushort)0); cw.Write((ushort)0); cw.Write((ushort)0); cw.Write(0u); cw.Write(offset); cw.Write(name); central.Add(record.ToArray());
                }
            }
            uint directory = (uint)stream.Position;
            foreach (byte[] record in central) writer.Write(record);
            uint size = (uint)stream.Position - directory;
            writer.Write(0x06054b50u); writer.Write((ushort)0); writer.Write((ushort)0); writer.Write((ushort)entries.Count); writer.Write((ushort)entries.Count); writer.Write(size); writer.Write(directory); writer.Write((ushort)0);
            writer.Flush(); stream.Flush(true);
        }
        return count;
    }
    internal static void Safe(string path) {
        string current = Path.GetFullPath(path);
        while (!String.IsNullOrEmpty(current)) {
            if (File.Exists(current) || Directory.Exists(current)) Require((File.GetAttributes(current) & FileAttributes.ReparsePoint) == 0, "Reparse point rejected");
            current = Path.GetDirectoryName(current);
        }
    }
    internal static bool Owned(string path) {
        Safe(path);
        using (var stream = File.OpenRead(path)) using (var zip = new ZipArchive(stream, ZipArchiveMode.Read)) {
            var entry = zip.GetEntry("meta.xml"); Require(entry != null && entry.Length <= 8192, "Invalid optional package metadata");
            using (var reader = XmlReader.Create(entry.Open(), new XmlReaderSettings { DtdProcessing = DtdProcessing.Prohibit, XmlResolver = null })) {
                var xml = new XmlDocument { XmlResolver = null }; xml.Load(reader);
                return xml.SelectSingleNode("/root/id") != null && xml.SelectSingleNode("/root/id").InnerText == ModId;
            }
        }
    }
    static bool Current(string path, string packages) {
        if (!File.Exists(path) || !Owned(path)) return false;
        using (var stream = File.OpenRead(path)) using (var zip = new ZipArchive(stream, ZipArchiveMode.Read))
        using (var reader = XmlReader.Create(zip.GetEntry("meta.xml").Open(), new XmlReaderSettings { DtdProcessing = DtdProcessing.Prohibit, XmlResolver = null })) {
            var xml = new XmlDocument { XmlResolver = null }; xml.Load(reader);
            var source = xml.SelectSingleNode("/root/sources");
            return source != null && source.InnerText == SourceStamp(packages);
        }
    }
    internal static string ModDirectory(string root, string version) {
        Require(Regex.IsMatch(version, @"\A\d+\.\d+\.\d+\.\d+\z"), "Invalid fog client version");
        string folder = version, paths = Path.Combine(root, "paths.xml");
        if (File.Exists(paths)) {
            var xml = new XmlDocument(); xml.XmlResolver = null; xml.Load(paths);
            var matches = new HashSet<string>(StringComparer.Ordinal);
            foreach (XmlNode node in xml.SelectNodes("/root/Paths/Path")) {
                string value = node.InnerText.Trim().Replace('\\', '/');
                foreach (string name in new[] { version, version + " Common Test" }) {
                    if (value == "./mods/" + name || value == "mods/" + name) matches.Add(name);
                }
            }
            Require(matches.Count == 1, "Missing or ambiguous client mod path");
            foreach (string name in matches) folder = name;
        }
        string directory = Path.Combine(root, "mods", folder);
        Require(Directory.Exists(directory), "Client mod version directory missing");
        return directory;
    }
    internal static void Apply(string root, string version, bool enabled, string stage) {
        string target = Path.Combine(ModDirectory(root, version), FileName), ready = Path.Combine(stage, "fog.ready");
        Safe(target); Safe(ready); Safe(Path.Combine(root, "res", "packages"));
        Require(Directory.Exists(Path.GetDirectoryName(target)), "Client mod version directory missing");
        if (File.Exists(target)) Require(Owned(target), "Optional package belongs to another mod");
        if (!enabled) { NoGame(root); if (File.Exists(target)) File.Delete(target); return; }
        string packages = Path.Combine(root, "res", "packages");
        if (!Current(ready, packages)) {
            if (File.Exists(ready)) File.Delete(ready);
            Build(packages, ready);
        }
        NoGame(root); Safe(target); Require(!File.Exists(target) || Owned(target), "Optional package changed");
        if (File.Exists(target)) File.Replace(ready, target, null); else File.Move(ready, target);
    }
    [DllImport("kernel32.dll", SetLastError = true)]
    static extern IntPtr OpenProcess(uint access, bool inherit, int pid);
    [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
    static extern bool QueryFullProcessImageName(IntPtr process, uint flags, StringBuilder name, ref int size);
    [DllImport("kernel32.dll")]
    static extern uint WaitForSingleObject(IntPtr handle, uint milliseconds);
    [DllImport("kernel32.dll")]
    static extern bool CloseHandle(IntPtr handle);
    static void NoGame(string root) {
        foreach (var process in Process.GetProcessesByName("WorldOfTanks")) using (process) {
            // Limited query works for elevated clients; MainModule throws for them and for exited ones.
            IntPtr handle = OpenProcess(0x00100000 | 0x1000, false, process.Id); // SYNCHRONIZE | QUERY_LIMITED_INFORMATION
            if (handle == IntPtr.Zero) {
                Require(Marshal.GetLastWin32Error() == 87, "Cannot inspect a running client"); // 87: process already gone
                continue;
            }
            try {
                if (WaitForSingleObject(handle, 0) == 0) continue; // exited, handle still enumerated
                var image = new StringBuilder(32768); int length = image.Capacity;
                Require(QueryFullProcessImageName(handle, 0, image, ref length), "Cannot inspect a running client");
                Require(!image.ToString().StartsWith(root + Path.DirectorySeparatorChar, StringComparison.OrdinalIgnoreCase), "Another client from this installation is running");
            } finally { CloseHandle(handle); }
        }
    }
    static string Selection(string stage) {
        string[] requests = Directory.GetFiles(stage, "request-*"); Array.Sort(requests, StringComparer.Ordinal);
        for (int i = requests.Length - 1; i >= 0; --i) {
            var match = Regex.Match(Path.GetFileName(requests[i]), @"\Arequest-\d{8}\.(on|off)\z");
            if (match.Success) { Safe(requests[i]); return match.Groups[1].Value; }
        }
        throw new InvalidDataException("Fog selection missing");
    }
    static int Main(string[] args) {
        string stage = null;
        bool validated = false;
        try {
            Require(args.Length == 3 && Regex.IsMatch(args[1], @"\A\d+\.\d+\.\d+\.\d+\z"), "Invalid arguments");
            int pid = Int32.Parse(args[0]); string version = args[1]; stage = Path.GetFullPath(args[2]);
            using (var parent = Process.GetProcessById(pid)) {
                string executable = parent.MainModule.FileName, bin = Path.GetDirectoryName(executable), root = Path.GetDirectoryName(bin);
                Require(Path.GetFileName(executable).Equals("WorldOfTanks.exe", StringComparison.OrdinalIgnoreCase) && (Path.GetFileName(bin) == "win64" || Path.GetFileName(bin) == "win32"), "Unexpected parent client");
                string cache = Path.Combine(root, "mods", "configs", "driftkings", "cache", "fog");
                Require(String.Equals(Path.GetDirectoryName(stage), cache, StringComparison.OrdinalIgnoreCase) && Path.GetFileName(stage) == "session-" + pid, "Stage outside owned cache");
                Require(String.Equals(System.Reflection.Assembly.GetExecutingAssembly().Location, Path.Combine(stage, "Driftkings.FogPackage.exe"), StringComparison.OrdinalIgnoreCase), "Helper outside owned stage");
                Safe(stage); Safe(cache);
                validated = true;
                bool restart = false;
                using (var gate = new FileStream(Path.Combine(cache, "install.lock"), FileMode.OpenOrCreate, FileAccess.ReadWrite, FileShare.None)) {
                    bool prepared = false;
                    do {
                        string selection = Selection(stage);
                        string ready = Path.Combine(stage, "fog.ready"); Safe(ready);
                        if (selection == "on" && !File.Exists(ready)) Build(Path.Combine(root, "res", "packages"), ready);
                        if (!prepared) { File.WriteAllText(Path.Combine(stage, "prepared"), "1"); prepared = true; }
                    } while (!parent.WaitForExit(200));
                    string consent = Path.Combine(stage, "restart"); Safe(consent);
                    if (File.Exists(consent)) {
                        Require(new FileInfo(consent).Length <= 32 && File.ReadAllText(consent).Trim() == pid.ToString(), "Invalid restart consent");
                        File.Delete(consent); restart = true;
                    }
                    string value = Selection(stage);
                    Apply(root, version, value == "on", stage);
                    File.WriteAllText(Path.Combine(stage, "result"), version + ":ok:" + value);
                }
                if (restart) {
                    ExitWork.Wait(root, Safe);
                    NoGame(root); Safe(executable);
                    var options = new ProcessStartInfo(executable) { UseShellExecute = false, CreateNoWindow = true, WorkingDirectory = root };
                    using (var process = Process.Start(options)) Require(process != null, "Could not reopen client");
                }
            }
            return 0;
        } catch (Exception error) {
            if (validated) try { Safe(stage); File.WriteAllText(Path.Combine(stage, "result"), args[1] + ":error:" + error.Message); } catch { }
            return 1;
        }
    }
}
