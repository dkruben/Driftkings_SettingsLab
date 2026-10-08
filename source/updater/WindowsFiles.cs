// Owned local Windows path/receipt operations. No network, scripts or shell.
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text;
using System.Threading;

internal static class WindowsFiles
{
    [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
    static extern uint GetFileAttributesW(string path);
    [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
    static extern IntPtr CreateFileW(string path, uint access, uint share, IntPtr security, uint disposition, uint flags, IntPtr template);
    [DllImport("kernel32.dll", SetLastError=true)]
    static extern bool CloseHandle(IntPtr handle);
    [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
    static extern bool ReplaceFileW(string target, string source, string backup, uint flags, IntPtr exclude, IntPtr reserved);
    static readonly UTF8Encoding Utf8 = new UTF8Encoding(false, true);
    static string root;

    sealed class Failure : Exception {
        internal readonly int Code;
        internal Failure(string message, int code=1001) : base(message) { Code=code; }
    }
    static void Require(bool valid, string message) { if (!valid) throw new Failure(message); }
    static string Decode(string value) {
        Require(value.Length<=16384, "Path exceeds limit");
        return Utf8.GetString(Convert.FromBase64String(value));
    }
    static string Canonical(string path, bool boundary=true) {
        Require(path!=null && path.Length>=3 && path.Length<4096, "Invalid path length");
        path=path.Replace('/', '\\');
        Require(Char.IsLetter(path[0]) && path[1]==':' && path[2]=='\\', "Absolute local drive required");
        Require(path.IndexOf(':',2)<0 && path.IndexOfAny(new char[]{'\0','*','?','<','>','|','"'})<0, "Invalid path characters/namespace");
        foreach (string part in path.Substring(3).Split('\\')) {
            Require(part!=".." && part!="." && !part.EndsWith(".") && !part.EndsWith(" "), "Noncanonical path component");
            string device=part.Split('.')[0].ToUpperInvariant();
            Require(device!="CON" && device!="PRN" && device!="AUX" && device!="NUL" &&
                    !(device.Length==4 && (device.StartsWith("COM") || device.StartsWith("LPT")) && device[3]>='1' && device[3]<='9'),"Device filename rejected");
            foreach(char c in part) Require(c>=32, "Control character in path");
        }
        string full=Path.GetFullPath(path).TrimEnd('\\');
        if(full.Length==2) full+="\\";
        if(boundary) Require(String.Equals(full,root,StringComparison.OrdinalIgnoreCase) || full.StartsWith(root.TrimEnd('\\')+"\\",StringComparison.OrdinalIgnoreCase), "Path escapes owned root");
        return full;
    }
    sealed class Guard : IDisposable {
        readonly List<IntPtr> handles=new List<IntPtr>();
        internal Guard(string path, bool requireFile=false) {
            try {
                List<string> paths=new List<string>();
                for(string p=path;p!=null;p=Path.GetDirectoryName(p)) paths.Add(p);
                paths.Reverse();
                foreach(string p in paths) {
                    uint attrs=GetFileAttributesW(p);
                    if(attrs==0xffffffff) {
                        int error=Marshal.GetLastWin32Error();
                        if(error==2 || error==3) { if(p==path && requireFile) throw new Failure("Required file missing",error); continue; }
                        throw new Failure("Cannot verify attributes",error);
                    }
                    Require((attrs&0x400)==0,"Reparse point rejected");
                    if(p==path && requireFile) Require((attrs&0x10)==0,"Regular file required");
                    // Lock directory ancestors against rename/delete and writes to their
                    // reparse metadata for the entire operation. File leafs may be
                    // replaced by ReplaceFileW; no copy/truncate fallback is allowed.
                    if((attrs&0x10)!=0) {
                        IntPtr h=CreateFileW(p,0x80,1,IntPtr.Zero,3,0x02200000,IntPtr.Zero);
                        if(h==new IntPtr(-1)) throw new Failure("Cannot lock ancestor",Marshal.GetLastWin32Error());
                        handles.Add(h);
                        uint again=GetFileAttributesW(p);
                        Require(again!=0xffffffff && (again&0x400)==0,"Ancestor changed/reparse");
                    }
                }
            } catch { Dispose(); throw; }
        }
        public void Dispose() { for(int i=handles.Count-1;i>=0;i--) CloseHandle(handles[i]); handles.Clear(); }
    }
    static void Validate(string path) { using(Guard guard=new Guard(Canonical(path))) {} }
    static void Replace(string source,string target) {
        source=Canonical(source); target=Canonical(target);
        string directory=Path.GetDirectoryName(target);
        Require(String.Equals(directory,Path.GetDirectoryName(source),StringComparison.OrdinalIgnoreCase),"Replacement must stay in one directory/volume");
        Require(Path.GetFileName(target)=="notified.json" && Path.GetFileName(source).StartsWith("notice-",StringComparison.Ordinal),"Only owned notification receipt replacement allowed");
        string normalized=directory.Replace('\\','/');
        Require(normalized.IndexOf("/mods/configs/Driftkings/cache/update/download-",StringComparison.OrdinalIgnoreCase)>=0 &&
                Path.GetFileName(directory).StartsWith("download-",StringComparison.Ordinal),"Owned transaction directory required");
        using(Guard a=new Guard(source,true)) using(Guard b=new Guard(target,true)) {
            Require((GetFileAttributesW(target)&1)==0,"Read-only target rejected");
            // Caller already flushed and closed. Repeat the local disk flush before
            // replacement, without creating or truncating either file.
            using(FileStream stream=new FileStream(source,FileMode.Open,FileAccess.ReadWrite,FileShare.Read)) stream.Flush(true);
            if(!ReplaceFileW(target,source,null,0,IntPtr.Zero,IntPtr.Zero)) throw new Failure("Atomic replacement failed",Marshal.GetLastWin32Error());
        }
    }
    static string Hash(string path) {
        using(FileStream stream=File.OpenRead(path)) using(SHA256 algorithm=SHA256.Create())
            return BitConverter.ToString(algorithm.ComputeHash(stream)).Replace("-","").ToLowerInvariant();
    }
    static string Line() {
        StringBuilder text=new StringBuilder();
        for(int i=0;i<=32768;i++) { int c=Console.In.Read(); if(c<0) { Require(text.Length==0,"Truncated request"); return null; } if(c=='\n') return text.ToString(); Require(c!='\r',"Invalid framing"); text.Append((char)c); }
        throw new Failure("Request exceeds limit");
    }
    static void Reply(string text) { Console.Out.WriteLine(text); Console.Out.Flush(); }
    static int Main(string[] args) {
        try {
            Require(args.Length==4 && args[0]=="--serve","Fixed protocol required");
            root=Canonical(args[1],false);
            Require(Directory.Exists(root),"Owned root missing");
            string self=System.Reflection.Assembly.GetExecutingAssembly().Location;
            Canonical(self);
            Validate(root); Validate(self);
            Require(args[3].Length==64 && Hash(self)==args[3],"Helper identity mismatch");
            int parentPid=Int32.Parse(args[2]); Require(parentPid>0 && parentPid!=Process.GetCurrentProcess().Id,"Invalid parent");
            Process parent=Process.GetProcessById(parentPid);
            Thread watcher=new Thread(delegate(){ try { parent.WaitForExit(); } catch {} Environment.Exit(0); });
            watcher.IsBackground=true; watcher.Start();
            Reply("READY\t1");
            string line;
            while((line=Line())!=null) {
                try {
                    string[] fields=line.Split('\t');
                    if(fields.Length==2 && fields[0]=="V") Validate(Decode(fields[1]));
                    else if(fields.Length==3 && fields[0]=="R") Replace(Decode(fields[1]),Decode(fields[2]));
                    else throw new Failure("Unknown operation");
                    Reply("OK\t"+fields[0]);
                } catch(Exception error) {
                    Failure failure=error as Failure;
                    Reply("ERR\t"+(failure!=null?failure.Code:1002)+"\t"+Convert.ToBase64String(Utf8.GetBytes(error.Message)));
                }
            }
            return 0;
        } catch(Exception error) { Console.Error.WriteLine(error.Message); return 1; }
    }
}
