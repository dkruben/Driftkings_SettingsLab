// Owned, offline Windows installer. No downloads, shell commands or restart.
// Requires the Windows .NET Framework 4.5+ runtime (ZipArchive).
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.IO.Compression;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;
using System.Web.Script.Serialization;
using System.Xml;

internal static class Installer
{
    [DllImport("kernel32.dll", SetLastError = true)]
    static extern IntPtr OpenProcess(uint access, bool inherit, int pid);
    [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
    static extern bool QueryFullProcessImageName(IntPtr process, uint flags, StringBuilder name, ref int size);
    [DllImport("kernel32.dll", SetLastError = true)]
    static extern uint WaitForSingleObject(IntPtr handle, uint milliseconds);
    [DllImport("kernel32.dll")]
    static extern bool CloseHandle(IntPtr handle);

    static readonly JavaScriptSerializer Json = new JavaScriptSerializer { MaxJsonLength = 65536, RecursionLimit = 10 };
    static string stage;

    static void Require(bool valid, string message)
    {
        if (!valid) throw new InvalidDataException(message);
    }

    static bool Same(string a, string b)
    {
        return String.Equals(Path.GetFullPath(a), Path.GetFullPath(b), StringComparison.OrdinalIgnoreCase);
    }

    static void Safe(string path, bool exists)
    {
        path = Path.GetFullPath(path);
        Require(Path.GetPathRoot(path).Length == 3 && path[1] == ':', "Local drive required");
        if (exists) Require(File.Exists(path) || Directory.Exists(path), "Missing owned path");
        for (string current = path; current != null; current = Path.GetDirectoryName(current))
        {
            // GetFileAttributes also detects links whose target is missing.
            try
            {
                Require((File.GetAttributes(current) & FileAttributes.ReparsePoint) == 0, "Reparse point rejected");
            }
            catch (FileNotFoundException) { }
            catch (DirectoryNotFoundException) { }
        }
    }

    static string Hash(Stream stream)
    {
        stream.Position = 0;
        using (var sha = SHA256.Create())
            return BitConverter.ToString(sha.ComputeHash(stream)).Replace("-", "").ToLowerInvariant();
    }

    static bool Matches(string path, long size, string sha)
    {
        Safe(path, false);
        if (!File.Exists(path)) return false;
        using (var input = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.Read))
            return input.Length == size && Hash(input) == sha;
    }

    static void Package(Stream input, string version)
    {
        input.Position = 0;
        using (var zip = new ZipArchive(input, ZipArchiveMode.Read, true))
        {
            Require(zip.Entries.Count <= 5000, "Too many package entries");
            var names = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            long total = 0;
            int mods = 0;
            foreach (var entry in zip.Entries)
            {
                string name = entry.FullName;
                Require(names.Add(name) && !name.StartsWith("/") && !name.Contains("\\") && !name.Contains(":"), "Invalid package path");
                Require(Array.IndexOf(name.Split('/'), "..") < 0, "Invalid package traversal");
                total += entry.Length;
                Require(total <= 128L * 1024 * 1024, "Package exceeds expanded limit");
                if (name.StartsWith("res/scripts/client/gui/mods/mod_", StringComparison.Ordinal))
                {
                    mods++;
                    Require(name == "res/scripts/client/gui/mods/mod_Driftkings.pyc", "Unexpected entry point");
                    using (var code = entry.Open())
                        Require(code.ReadByte() == 3 && code.ReadByte() == 243 && code.ReadByte() == 13 && code.ReadByte() == 10, "Wrong bytecode");
                }
            }
            Require(mods == 1, "Missing entry point");
            var meta = zip.GetEntry("meta.xml");
            Require(meta != null && meta.Length <= 8192, "Invalid metadata");
            using (var stream = meta.Open())
            using (var reader = XmlReader.Create(stream, new XmlReaderSettings { DtdProcessing = DtdProcessing.Prohibit, XmlResolver = null }))
            {
                var document = new XmlDocument { XmlResolver = null };
                document.Load(reader);
                Require(document.DocumentElement.Name == "root" && document.SelectSingleNode("/root/id").InnerText == "driftkings.unified" &&
                        document.SelectSingleNode("/root/version").InnerText == version, "Wrong package identity/version");
            }
        }
    }

    static void Result(string status, string error)
    {
        Safe(stage, true);
        string temporary = Path.Combine(stage, "result.json.tmp");
        string destination = Path.Combine(stage, "result.json");
        Safe(temporary, false); Safe(destination, false);
        using (var output = new FileStream(temporary, FileMode.Create, FileAccess.Write, FileShare.None))
        {
            byte[] bytes = Encoding.UTF8.GetBytes(Json.Serialize(new { schema = 1, status = status, error = error,
                                                                        helperPid = Process.GetCurrentProcess().Id }));
            output.Write(bytes, 0, bytes.Length);
            output.Flush(true);
        }
        if (File.Exists(destination)) File.Replace(temporary, destination, null);
        else File.Move(temporary, destination);
    }

    static Dictionary<string, object> Ticket()
    {
        string path = Path.Combine(stage, "install.json");
        Safe(path, true);
        Require(new FileInfo(path).Length <= 65536, "Ticket exceeds limit");
        var value = Json.Deserialize<Dictionary<string, object>>(File.ReadAllText(path, Encoding.UTF8));
        string[] keys = { "schema", "gameVersion", "version", "size", "sha256", "installedVersion", "installedSize", "installedSha256" };
        Require(value.Count == keys.Length, "Invalid ticket fields");
        foreach (var key in keys) Require(value.ContainsKey(key), "Missing ticket field");
        Require(value["schema"] is int && (int)value["schema"] == 1, "Invalid ticket schema");
        Require(value["gameVersion"] is string && Regex.IsMatch((string)value["gameVersion"], @"\A(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\z"), "Invalid game version");
        foreach (string key in new[] { "sha256", "installedSha256" })
            Require(value[key] is string && Regex.IsMatch((string)value[key], @"\A[0-9a-f]{64}\z"), "Invalid hash");
        foreach (string key in new[] { "size", "installedSize" })
            Require(value[key] is int && (int)value[key] > 0 && (int)value[key] <= 64 * 1024 * 1024, "Invalid size");
        foreach (string key in new[] { "version", "installedVersion" })
            Require(value[key] is string && ((string)value[key]).Length <= 200, "Invalid version");
        return value;
    }

    static void NoGame()
    {
        // Includes a WGC restart or another WoT instance: defer rather than race it.
        foreach (var process in Process.GetProcessesByName("WorldOfTanks"))
        {
            using (process) Require(process.HasExited, "WoT is running; installation deferred");
        }
    }

    internal static void ReplaceVerified(string target, string temporary, string backup,
                                         Action verifyNew, Func<string, bool> validOld,
                                         Action beforeRollback, Action committed, Action rolledBack)
    {
        bool replaced = false;
        try
        {
            File.Replace(temporary, target, backup);
            replaced = true;
            verifyNew();
            committed();
        }
        catch
        {
            if (replaced)
            {
                Require(validOld(backup), "Rollback backup mismatch");
                beforeRollback();
                File.Replace(backup, target, null);
                Require(validOld(target), "Rollback verification failed");
                rolledBack();
            }
            throw;
        }
    }

    static int Apply(string root, Dictionary<string, object> ticket, Stream ready)
    {
        string target = Path.Combine(root, "mods", (string)ticket["gameVersion"], "Driftkings.wotmod");
        string backup = target + ".old";
        string temporary = target + ".new";
        long size = (int)ticket["size"], oldSize = (int)ticket["installedSize"];
        string sha = (string)ticket["sha256"], oldSha = (string)ticket["installedSha256"];
        Safe(Path.GetDirectoryName(target), true);
        Safe(target, false); Safe(backup, false); Safe(temporary, false);
        NoGame();
        // Crash recovery: File.Replace leaves the complete old file in .old.
        // Keep that backup if its provenance does not match this transaction.
        if (File.Exists(backup))
        {
            Require(Matches(backup, oldSize, oldSha), "Backup does not match transaction");
            using (var old = new FileStream(backup, FileMode.Open, FileAccess.Read, FileShare.Read))
                Package(old, (string)ticket["installedVersion"]);
            if (Matches(target, size, sha))
            {
                NoGame(); File.Delete(backup); Result("installed", null); return 0;
            }
            NoGame();
            if (File.Exists(target)) File.Replace(backup, target, null);
            else File.Move(backup, target);
            Require(Matches(target, oldSize, oldSha), "Recovery verification failed");
            Result("rolledBack", "interruptedInstall"); return 2;
        }
        Require(Matches(target, oldSize, oldSha), "Installed package changed; refusing replacement");
        using (var old = new FileStream(target, FileMode.Open, FileAccess.Read, FileShare.Read))
            Package(old, (string)ticket["installedVersion"]);
        try
        {
            // Same-volume destination; staging is retained for retries/recovery.
            using (var output = new FileStream(temporary, FileMode.CreateNew, FileAccess.Write, FileShare.None))
            {
                ready.Position = 0;
                ready.CopyTo(output, 65536);
                output.Flush(true);
            }
            Require(Matches(temporary, size, sha), "Copied package hash mismatch");
            NoGame(); Safe(target, true); Safe(temporary, true); Safe(backup, false);
            Require(Matches(target, oldSize, oldSha), "Installed package changed during preparation");
            Result("installing", null);
            ReplaceVerified(target, temporary, backup,
                            () => Require(Matches(target, size, sha), "Final verification failed"),
                            path => Matches(path, oldSize, oldSha), NoGame,
                            () => Result("installed", null), () => Result("rolledBack", "installFailed"));
            // Cleanup is outside the transaction. A locked backup is retained
            // for recovery without undoing a verified successful installation.
            try { Safe(backup, true); File.Delete(backup); }
            catch (IOException) { }
            catch (UnauthorizedAccessException) { }
            return 0;
        }
        finally
        {
            Safe(temporary, false);
            if (File.Exists(temporary)) File.Delete(temporary);
        }
    }

    static int Main(string[] args)
    {
        IntPtr parent = IntPtr.Zero;
        FileStream gate = null;
        bool owned = false;
        try
        {
            Require(args.Length == 2, "Expected owned stage and parent PID");
            stage = Path.GetFullPath(args[0]);
            int pid; Require(Int32.TryParse(args[1], out pid) && pid > 0, "Invalid PID");
            parent = OpenProcess(0x00100000 | 0x1000, false, pid); // SYNCHRONIZE | QUERY_LIMITED_INFORMATION
            Require(parent != IntPtr.Zero, "Parent process unavailable");
            var image = new StringBuilder(32768); int length = image.Capacity;
            Require(QueryFullProcessImageName(parent, 0, image, ref length), "Cannot validate parent image");
            string executable = image.ToString(), binaryFolder = Path.GetDirectoryName(executable);
            Require(String.Equals(Path.GetFileName(executable), "WorldOfTanks.exe", StringComparison.OrdinalIgnoreCase) &&
                    (Path.GetFileName(binaryFolder) == "win64" || Path.GetFileName(binaryFolder) == "win32"), "Unexpected parent image");
            string root = Path.GetDirectoryName(binaryFolder);
            string cache = Path.Combine(root, "mods", "configs", "Driftkings", "cache", "update");
            Require(Same(Path.GetDirectoryName(stage), cache) && Path.GetFileName(stage).StartsWith("download-", StringComparison.Ordinal), "Stage outside owned cache");
            Safe(executable, true); Safe(stage, true);
            Require(Same(Assembly.GetExecutingAssembly().Location, Path.Combine(stage, "Driftkings.UpdateInstaller.exe")), "Helper outside stage");
            string lockPath = Path.Combine(cache, "install.lock"); Safe(lockPath, false);
            // Hold one OS lock for the whole wait/install; never delete its path.
            gate = new FileStream(lockPath, FileMode.OpenOrCreate, FileAccess.ReadWrite, FileShare.None);
            {
                owned = true;
                var ticket = Ticket();
                string readyPath = Path.Combine(stage, "Driftkings.wotmod.ready"); Safe(readyPath, true);
                using (var ready = new FileStream(readyPath, FileMode.Open, FileAccess.Read, FileShare.Read))
                {
                    Require(ready.Length == (int)ticket["size"] && Hash(ready) == (string)ticket["sha256"], "Staged package mismatch");
                    Package(ready, (string)ticket["version"]);
                    Result("prepared", null);
                    // Cooperative cancellation for unconfirmed preparation or
                    // a timeout. No permanent client-side loop is introduced.
                    string cancel = Path.Combine(stage, "cancel.install");
                    while (true)
                    {
                        Safe(cancel, false);
                        if (File.Exists(cancel)) { Result("cancelled", null); return 3; }
                        uint wait = WaitForSingleObject(parent, 200);
                        if (wait == 0) break;
                        Require(wait == 258, "Wait failed");
                    }
                    Safe(cancel, false);
                    if (File.Exists(cancel)) { Result("cancelled", null); return 3; }
                    return Apply(root, ticket, ready);
                }
            }
        }
        catch (Exception error)
        {
            // Fixed code only; no paths, credentials or exception text in result.
            if (owned)
            {
                try
                {
                    string path = Path.Combine(stage, "result.json");
                    string previous = File.Exists(path) ? File.ReadAllText(path) : "";
                    if (!previous.Contains("\"rolledBack\"") && !previous.Contains("\"installed\""))
                        Result("error", error is IOException ? "installIOError" : "installValidationError");
                }
                catch { } // Failed result IO cannot justify mutating game/config files.
            }
            return 1;
        }
        finally
        {
            if (gate != null) gate.Dispose();
            if (parent != IntPtr.Zero) CloseHandle(parent);
        }
    }
}
