// All component names, paths and option keys come from the generated include.
const
  LB_ITEMFROMPOINT = $01A9;

function GetDriveType(RootPath: String): Cardinal;
  external 'GetDriveTypeW@kernel32.dll stdcall';
function SetTimer(hWnd: HWND; nIDEvent, uElapse: LongWord; lpTimerFunc: LongWord): LongWord;
  external 'SetTimer@user32.dll stdcall';
function KillTimer(hWnd: HWND; uIDEvent: LongWord): BOOL;
  external 'KillTimer@user32.dll stdcall';
function GetCursorPos(var lpPoint: TPoint): BOOL;
  external 'GetCursorPos@user32.dll stdcall';
function ScreenToClient(hWnd: HWND; var lpPoint: TPoint): BOOL;
  external 'ScreenToClient@user32.dll stdcall';
var
  ResetConfig, ResetRequested, PreserveProfile: Boolean;
  Preview: TBitmapImage;
  SelectedRoot, ConfigBackup: String;
  Installations: TStringList;
  InstallationList: TNewComboBox;
  ClientNotice: TNewStaticText;
  Description, PreserveNotice: TNewStaticText;
  KeepProfileRadio, ResetProfileRadio: TNewRadioButton;
  HoverTimer: LongWord;
  PreviewIndex: Integer;

// AppId is finalized after validation, separately for every game root.
function InstallationId(Param: String): String;
begin
  Result := '';
  if SelectedRoot <> '' then
    Result := 'Driftkings.Modpack.' + GetSHA256OfString(Lowercase(SelectedRoot));
end;

function ConfigRoot: String;
begin
  // The directory page exists during InitializeWizard; {app} is not ready yet.
  Result := AddBackslash(WizardDirValue) + 'mods\configs\driftkings';
end;

function IsReparseDirectory(const Folder: String): Boolean;
var
  Item: TFindRec;
begin
  Result := False;
  if FindFirst(Folder, Item) then begin
    Result := (Item.Attributes and $400) <> 0;
    FindClose(Item);
  end;
end;

function ConfigurationPathError: String;
var
  Folder: String;
begin
  Result := '';
  if IsReparseDirectory(ConfigRoot + '\installer-backup') then begin
    Result := 'Installer backup path uses a reparse point';
    Exit;
  end;
  Folder := ConfigRoot;
  while CompareText(Folder, ExpandConstant('{app}')) <> 0 do begin
    if IsReparseDirectory(Folder) then begin
      Result := 'Configuration path uses a reparse point: ' + Folder;
      Exit;
    end;
    Folder := ExtractFileDir(Folder);
  end;
end;

function HasProfile: Boolean;
var
  Item, Child: TFindRec;
begin
  Result := FileExists(ConfigRoot + '\load.json') or
    FileExists(ConfigRoot + '\load.json.previous') or
    FileExists(ConfigRoot + '\driftkings.json') or DirExists(ConfigRoot + '\default');
  if Result then Exit;
  if FindFirst(ConfigRoot + '\*.json', Item) then begin
    Result := True;
    FindClose(Item);
    Exit;
  end;
  if not FindFirst(ConfigRoot + '\*', Item) then Exit;
  try
    repeat
      if ((Item.Attributes and FILE_ATTRIBUTE_DIRECTORY) <> 0) and
         (Item.Name <> '.') and (Item.Name <> '..') and
         (CompareText(Item.Name, 'cache') <> 0) and (CompareText(Item.Name, 'installer-backup') <> 0) and
         (CompareText(Item.Name, 'installer') <> 0) and (CompareText(Item.Name, 'SixthSense') <> 0) and
         (CompareText(Item.Name, 'images') <> 0) then
        if FindFirst(ConfigRoot + '\' + Item.Name + '\*.json', Child) then begin
          Result := True;
          FindClose(Child);
        end;
    until Result or not FindNext(Item);
  finally
    FindClose(Item);
  end;
end;

procedure ShowPreview(Index: Integer);
var
  AvailableWidth, AvailableHeight, Width, Height: Integer;
  Filename: String;
begin
  PreviewIndex := Index;
  Preview.Visible := False;
  Description.Caption := '';
  if (Index < 0) or (Index >= PreviewCount) then Exit;
  Description.Caption := CustomMessage(PreviewMessage(Index));
  Filename := PreviewFile(Index);
  if Filename = '' then Exit;
  try
    ExtractTemporaryFile(Filename);
    Preview.PngImage.LoadFromFile(ExpandConstant('{tmp}\') + Filename);
    AvailableWidth := WizardForm.SelectComponentsPage.ClientWidth - Preview.Left;
    AvailableHeight := WizardForm.ComponentsList.Height - Description.Height - ScaleY(12);
    Width := AvailableWidth;
    Height := Preview.PngImage.Height * Width div Preview.PngImage.Width;
    if Height > AvailableHeight then begin
      Height := AvailableHeight;
      Width := Preview.PngImage.Width * Height div Preview.PngImage.Height;
    end;
    Preview.Width := Width;
    Preview.Height := Height;
    Preview.Visible := True;
  except
    Log('Optional preview unavailable: ' + Filename);
  end;
end;

procedure UpdatePreview(Sender: TObject);
begin
  ShowPreview(WizardForm.ComponentsList.ItemIndex);
end;

procedure PreviewKeyUp(Sender: TObject; var Key: Word; Shift: TShiftState);
begin
  UpdatePreview(Sender);
end;

// The component under the mouse previews immediately; clicks and keys keep working as before.
procedure HoverTimerProc(Wnd: HWND; Msg: LongWord; IdEvent: LongWord; Time: LongWord);
var
  Point: TPoint;
  Item: LongInt;
  List: TNewCheckListBox;
begin
  if WizardForm.CurPageID <> wpSelectComponents then Exit;
  List := WizardForm.ComponentsList;
  if not GetCursorPos(Point) or not ScreenToClient(List.Handle, Point) then Exit;
  if (Point.X < 0) or (Point.Y < 0) or (Point.X >= List.ClientWidth) or (Point.Y >= List.ClientHeight) then Exit;
  Item := SendMessage(List.Handle, LB_ITEMFROMPOINT, 0, (Point.Y shl 16) or (Point.X and $FFFF));
  // The high word is non-zero when the point lies outside every item.
  if (Item shr 16) <> 0 then Exit;
  Item := Item and $FFFF;
  if (Item < List.Items.Count) and (Item <> PreviewIndex) then ShowPreview(Item);
end;

function XmlValue(const Data, Name: String): String;
var
  Start, Finish: Integer;
begin
  Result := '';
  Start := Pos('<' + Name + '>', Data);
  Finish := Pos('</' + Name + '>', Data);
  if (Start > 0) and (Finish > Start) then
    Result := Trim(Copy(Data, Start + Length(Name) + 2, Finish - Start - Length(Name) - 2));
end;

// Discovery is deliberately bounded: registry plus immediate game folders.
function GameRoot(Path: String): String;
var
  Parent: String;
begin
  Path := RemoveBackslashUnlessRoot(ExpandFileName(RemoveQuotes(Trim(Path))));
  if FileExists(Path) then Path := ExtractFileDir(Path);
  Result := '';
  while Length(Path) > 3 do begin
    if FileExists(Path + '\version.xml') and DirExists(Path + '\res\packages') and
       (FileExists(Path + '\WorldOfTanks.exe') or FileExists(Path + '\win64\WorldOfTanks.exe') or
        FileExists(Path + '\win32\WorldOfTanks.exe')) then begin
      Result := Path;
      Exit;
    end;
    Parent := ExtractFileDir(Path);
    if Parent = Path then Exit;
    Path := Parent;
  end;
end;

function ReadClient(const Folder: String; var Version, Realm: String): Boolean;
var
  Data: AnsiString;
  Hash: Integer;
begin
  Version := '';
  Realm := '';
  Result := LoadStringFromFile(Folder + '\version.xml', Data);
  if not Result then Exit;
  Version := XmlValue(String(Data), 'version');
  if Copy(Version, 1, 2) = 'v.' then Delete(Version, 1, 2);
  Hash := Pos(' #', Version);
  if Hash > 0 then Version := Copy(Version, 1, Hash - 1);
  Version := Trim(Version);
  Realm := Uppercase(XmlValue(String(Data), 'realm'));
  // SEA is the former name of the ASIA realm.
  if Realm = 'SEA' then Realm := 'ASIA';
  Result := (Version <> '') and (Realm <> '');
end;

function ClientError: String;
var
  Root, Version, Realm: String;
begin
  Result := CustomMessage('WrongClient');
  Root := GameRoot(WizardDirValue);
  if Root = '' then Exit;
  if not ReadClient(Root, Version, Realm) then Exit;
  if (Version <> '{#GameVersion}') or
     (Pos('|' + Realm + '|', '{#SupportedRealms}') = 0) then begin
    Result := Result + #13#10 + Format(CustomMessage('DetectedClient'), [Realm, Version, Root]);
    Exit;
  end;
  Result := '';
end;

// An existing profile is kept unless the user (or /RESETCONFIG=1) asks to choose components again.
procedure RefreshProfileChoice;
var
  Existing: Boolean;
begin
  Existing := HasProfile;
  PreserveNotice.Visible := Existing;
  KeepProfileRadio.Visible := Existing;
  ResetProfileRadio.Visible := Existing;
  ResetConfig := ResetRequested or (Existing and ResetProfileRadio.Checked);
end;

procedure ProfileChoiceClick(Sender: TObject);
begin
  RefreshProfileChoice;
end;

procedure RefreshClient(Sender: TObject);
var
  Root, Version, Realm: String;
begin
  Root := GameRoot(WizardDirValue);
  if (Root <> '') and ReadClient(Root, Version, Realm) then
    ClientNotice.Caption := Format(CustomMessage('DetectedClient'), [Realm, Version, Root])
  else ClientNotice.Caption := CustomMessage('ChooseRoot');
  RefreshProfileChoice;
end;

procedure SelectInstallation(Sender: TObject);
begin
  if InstallationList.ItemIndex >= 0 then
    WizardForm.DirEdit.Text := Installations[InstallationList.ItemIndex];
end;

procedure AddInstallation(const Candidate: String);
var
  Root, Version, Realm: String;
  I: Integer;
begin
  if Trim(Candidate) = '' then Exit;
  Root := GameRoot(Candidate);
  if (Root = '') or not ReadClient(Root, Version, Realm) then Exit;
  if Pos('|' + Realm + '|', '{#SupportedRealms}') = 0 then Exit;
  for I := 0 to Installations.Count - 1 do
    if CompareText(Installations[I], Root) = 0 then Exit;
  Installations.Add(Root);
  InstallationList.Items.Add(Realm + ' | ' + Version + ' | ' + Root);
end;

procedure RegistryInstallations(Hive: Integer);
var
  Names: TArrayOfString;
  I: Integer;
  Key, Name, Location: String;
begin
  Key := 'Software\Microsoft\windows\CurrentVersion\Uninstall';
  if not RegGetSubkeyNames(Hive, Key, Names) then Exit;
  for I := 0 to GetArrayLength(Names) - 1 do begin
    if RegQueryStringValue(Hive, Key + '\' + Names[I], 'DisplayName', Name) then
      if Pos('world of tanks', Lowercase(Name)) > 0 then
        if RegQueryStringValue(Hive, Key + '\' + Names[I], 'InstallLocation', Location) then
          AddInstallation(Location);
  end;
end;

procedure ScanGameFolders(const Folder: String);
var
  Item: TFindRec;
begin
  AddInstallation(Folder);
  if not FindFirst(AddBackslash(Folder) + '*', Item) then Exit;
  try
    repeat
      if ((Item.Attributes and FILE_ATTRIBUTE_DIRECTORY) <> 0) and
         ((Item.Attributes and $400) = 0) and
         (Pos('world', Lowercase(Item.Name)) > 0) then
        AddInstallation(AddBackslash(Folder) + Item.Name);
    until not FindNext(Item);
  finally
    FindClose(Item);
  end;
end;

procedure DiscoverInstallations;
var
  I, Match: Integer;
  Drive: String;
begin
  AddInstallation(WizardDirValue);
  RegistryInstallations(HKCU32);
  RegistryInstallations(HKLM32);
  if IsWin64 then begin
    RegistryInstallations(HKCU64);
    RegistryInstallations(HKLM64);
  end;
  for I := 67 to 90 do begin
    Drive := Chr(I) + ':\';
    // Only fixed local drives, never network or removable devices.
    if GetDriveType(Drive) = 3 then begin
      ScanGameFolders(Drive);
      ScanGameFolders(Drive + 'Games');
      ScanGameFolders(Drive + 'Wargaming.net');
      ScanGameFolders(Drive + 'Games\Wargaming.net');
    end;
  end;
  ScanGameFolders(ExpandConstant('{autopf}'));
  ScanGameFolders(ExpandConstant('{autopf}\Wargaming.net'));
  if IsWin64 then ScanGameFolders(ExpandConstant('{commonpf32}\Wargaming.net'));
  // Preserve an explicit /DIR or previous valid path; otherwise prefer a matching client.
  Match := -1;
  for I := 0 to Installations.Count - 1 do begin
    if CompareText(Installations[I], GameRoot(WizardDirValue)) = 0 then begin
      Match := I;
      Break;
    end;
  end;
  if (Match < 0) and (ExpandConstant('{param:DIR|}') = '') then
    for I := 0 to Installations.Count - 1 do
      if Pos(' | {#GameVersion} | ', InstallationList.Items[I]) > 0 then begin
        Match := I;
        Break;
      end;
  InstallationList.ItemIndex := Match;
  if Match >= 0 then SelectInstallation(InstallationList);
  RefreshClient(WizardForm.DirEdit);
end;

function NextButtonClick(CurPageID: Integer): Boolean;
var
  Error: String;
begin
  Result := True;
  if CurPageID <> wpSelectDir then Exit;
  Error := ClientError;
  Result := Error = '';
  if Result then begin
    WizardForm.DirEdit.Text := GameRoot(WizardDirValue);
    RefreshProfileChoice;
  end
  else MsgBox(Error, mbError, MB_OK);
end;

procedure InitializeWizard;
begin
  ResetRequested := ExpandConstant('{param:RESETCONFIG|0}') = '1';
  ResetConfig := ResetRequested;
  PreviewIndex := -1;
  WizardForm.ComponentsList.Width := WizardForm.ComponentsList.Width * 3 div 5;
  Description := TNewStaticText.Create(WizardForm);
  Description.Parent := WizardForm.SelectComponentsPage;
  Description.Left := WizardForm.ComponentsList.Left + WizardForm.ComponentsList.Width + ScaleX(12);
  Description.Top := WizardForm.ComponentsList.Top;
  Description.Width := WizardForm.SelectComponentsPage.ClientWidth - Description.Left;
  Description.Height := ScaleY(70);
  Description.AutoSize := False;
  Description.WordWrap := True;
  Preview := TBitmapImage.Create(WizardForm);
  Preview.Parent := WizardForm.SelectComponentsPage;
  Preview.Left := Description.Left;
  Preview.Top := Description.Top + Description.Height + ScaleY(12);
  Preview.Stretch := True;
  Preview.Visible := False;
  WizardForm.ComponentsList.OnClick := @UpdatePreview;
  WizardForm.ComponentsList.OnClickCheck := @UpdatePreview;
  WizardForm.ComponentsList.OnKeyUp := @PreviewKeyUp;
  PreserveNotice := TNewStaticText.Create(WizardForm);
  PreserveNotice.Parent := WizardForm.SelectDirPage;
  PreserveNotice.Left := WizardForm.DirEdit.Left;
  PreserveNotice.Top := WizardForm.SelectDirPage.ClientHeight - ScaleY(86);
  PreserveNotice.Width := WizardForm.SelectDirPage.ClientWidth - PreserveNotice.Left;
  PreserveNotice.Height := ScaleY(34);
  PreserveNotice.AutoSize := False;
  PreserveNotice.WordWrap := True;
  PreserveNotice.Caption := CustomMessage('ProfileFound');
  PreserveNotice.Visible := False;
  KeepProfileRadio := TNewRadioButton.Create(WizardForm);
  KeepProfileRadio.Parent := WizardForm.SelectDirPage;
  KeepProfileRadio.Left := PreserveNotice.Left;
  KeepProfileRadio.Top := PreserveNotice.Top + PreserveNotice.Height + ScaleY(4);
  KeepProfileRadio.Width := PreserveNotice.Width;
  KeepProfileRadio.Height := ScaleY(20);
  KeepProfileRadio.Caption := CustomMessage('KeepProfile');
  KeepProfileRadio.Checked := not ResetRequested;
  KeepProfileRadio.OnClick := @ProfileChoiceClick;
  KeepProfileRadio.Visible := False;
  ResetProfileRadio := TNewRadioButton.Create(WizardForm);
  ResetProfileRadio.Parent := WizardForm.SelectDirPage;
  ResetProfileRadio.Left := PreserveNotice.Left;
  ResetProfileRadio.Top := KeepProfileRadio.Top + KeepProfileRadio.Height + ScaleY(2);
  ResetProfileRadio.Width := PreserveNotice.Width;
  ResetProfileRadio.Height := ScaleY(20);
  ResetProfileRadio.Caption := CustomMessage('ResetProfile');
  ResetProfileRadio.Checked := ResetRequested;
  ResetProfileRadio.OnClick := @ProfileChoiceClick;
  ResetProfileRadio.Visible := False;
  Installations := TStringList.Create;
  InstallationList := TNewComboBox.Create(WizardForm);
  InstallationList.Parent := WizardForm.SelectDirPage;
  InstallationList.Left := WizardForm.DirEdit.Left;
  InstallationList.Top := WizardForm.DirEdit.Top + WizardForm.DirEdit.Height + ScaleY(12);
  InstallationList.Width := WizardForm.SelectDirPage.ClientWidth - InstallationList.Left;
  InstallationList.Style := csDropDownList;
  InstallationList.OnChange := @SelectInstallation;
  ClientNotice := TNewStaticText.Create(WizardForm);
  ClientNotice.Parent := WizardForm.SelectDirPage;
  ClientNotice.Left := InstallationList.Left;
  ClientNotice.Top := InstallationList.Top + InstallationList.Height + ScaleY(8);
  ClientNotice.Width := InstallationList.Width;
  ClientNotice.Height := ScaleY(55);
  ClientNotice.AutoSize := False;
  ClientNotice.WordWrap := True;
  WizardForm.DirEdit.OnChange := @RefreshClient;
  DiscoverInstallations;
  HoverTimer := SetTimer(0, 0, 150, CreateCallback(@HoverTimerProc));
end;

procedure DeinitializeSetup;
begin
  if HoverTimer <> 0 then KillTimer(0, HoverTimer);
end;

// Finished page: what was installed, for which client, and what happened to the profile.
function InstallSummary: String;
var
  Version, Realm: String;
begin
  Result := Format(CustomMessage('SummaryInstalled'), ['{#BuildVersion}', '{#GameVersion}']);
  if ReadClient(SelectedRoot, Version, Realm) then
    Result := Result + #13#10 + Format(CustomMessage('DetectedClient'), [Realm, Version, SelectedRoot]);
  if PreserveProfile then Result := Result + #13#10#13#10 + CustomMessage('SummaryPreserved')
  else if ConfigBackup <> '' then Result := Result + #13#10#13#10 + Format(CustomMessage('SummaryReset'), [ConfigBackup])
  else Result := Result + #13#10#13#10 + CustomMessage('SummaryCreated');
  Result := Result + #13#10#13#10 + CustomMessage('SummaryNext');
end;

// Before any click or hover, show the first component that has artwork.
function FirstPreviewIndex: Integer;
var
  I: Integer;
begin
  Result := 0;
  for I := 0 to PreviewCount - 1 do
    if PreviewFile(I) <> '' then begin
      Result := I;
      Exit;
    end;
end;

procedure CurPageChanged(CurPageID: Integer);
begin
  if CurPageID = wpSelectComponents then
    if WizardForm.ComponentsList.ItemIndex >= 0 then UpdatePreview(WizardForm.ComponentsList)
    else ShowPreview(FirstPreviewIndex);
  if CurPageID = wpFinished then begin
    WizardForm.FinishedLabel.Caption := InstallSummary;
    WizardForm.AdjustLabelHeight(WizardForm.FinishedLabel);
  end;
end;

function ShouldSkipPage(PageID: Integer): Boolean;
begin
  Result := ((PageID = wpSelectComponents) or (PageID = wpSelectTasks)) and HasProfile and not ResetConfig;
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  Locator, Services, Processes: Variant;
begin
  Result := ClientError;
  if Result <> '' then Exit;
  WizardForm.DirEdit.Text := GameRoot(WizardDirValue);
  Result := ExistingDependenciesError;
  if Result <> '' then Exit;
  Result := ConfigurationPathError;
  if Result <> '' then Exit;
  Result := CustomMessage('ProcessCheckFailed');
  try
    Locator := CreateOleObject('WbemScripting.SWbemLocator');
    Services := Locator.ConnectServer('', 'root\cimv2');
    Processes := Services.ExecQuery('SELECT ProcessId FROM Win32_Process WHERE Name = ''WorldOfTanks.exe''');
    if Processes.Count > 0 then begin
      Result := CustomMessage('CloseGame');
      Exit;
    end;
  except
    Exit;
  end;
  SelectedRoot := GameRoot(WizardDirValue);
  PreserveProfile := HasProfile and not ResetConfig;
  Result := '';
end;

procedure CollectConfigs(const Folder, Relative: String; Files: TStringList);
var
  Item: TFindRec;
  Child, Name: String;
begin
  if not FindFirst(AddBackslash(Folder) + '*', Item) then Exit;
  try
    repeat
      Name := Item.Name;
      if (Name <> '.') and (Name <> '..') then begin
        Child := AddBackslash(Relative) + Name;
        if Relative = '' then Child := Name;
        if (Relative <> '') or ((CompareText(Name, 'installer-backup') <> 0) and
           (CompareText(Name, 'cache') <> 0) and (CompareText(Name, 'installer') <> 0) and
           (CompareText(Name, 'images') <> 0) and (CompareText(Name, 'SixthSense') <> 0)) then begin
          if (Item.Attributes and $400) <> 0 then RaiseException('Cannot reset configurations through a reparse point');
          if (Item.Attributes and FILE_ATTRIBUTE_DIRECTORY) <> 0 then
            CollectConfigs(AddBackslash(Folder) + Name, Child, Files)
          else if (CompareText(ExtractFileExt(Name), '.json') = 0) or
                  (Pos('.json.previous', Lowercase(Name)) > 0) or (Pos('.json.bak', Lowercase(Name)) > 0) then
            Files.Add(Child);
        end;
      end;
    until not FindNext(Item);
  finally
    FindClose(Item);
  end;
end;

procedure WriteNewConfig(const Path, Data: String; Created: TStringList);
var
  Temporary: String;
begin
  if FileExists(Path) then RaiseException('Refusing to overwrite configuration: ' + Path);
  if not ForceDirectories(ExtractFileDir(Path)) then RaiseException('Cannot create configuration directory');
  Temporary := Path + '.installer-new';
  if FileExists(Temporary) then RaiseException('A previous installer write is still present');
  if not SaveStringToFile(Temporary, Data + #13#10, False) then RaiseException('Cannot write configuration');
  if not RenameFile(Temporary, Path) then begin
    DeleteFile(Temporary);
    RaiseException('Cannot publish configuration');
  end;
  Created.Add(Path);
end;

function JsonBool(Value: Boolean): String;
begin
  if Value then Result := 'true' else Result := 'false';
end;

procedure WriteChoices(Created: TStringList);
var
  Files: TStringList;
  I, J: Integer;
  Body, Filename: String;
begin
  Files := TStringList.Create;
  try
    for I := 0 to ChoiceCount - 1 do
      if Files.IndexOf(ChoiceFile(I)) < 0 then Files.Add(ChoiceFile(I));
    for I := 0 to Files.Count - 1 do begin
      Body := '';
      Filename := Files[I];
      for J := 0 to ChoiceCount - 1 do
        if (ChoiceFile(J) = Filename) and (ChoiceSelected(J) <> ChoiceDefault(J)) then begin
          if Body <> '' then Body := Body + ',' + #13#10;
          Body := Body + '  "' + ChoiceKey(J) + '": ' + JsonBool(ChoiceSelected(J));
        end;
      if Body <> '' then WriteNewConfig(ConfigRoot + '\' + Filename, '{' + #13#10 + Body + #13#10 + '}', Created);
    end;
    WriteNewConfig(ConfigRoot + '\load.json', '{"loadConfig":"default"}', Created);
    if not ForceDirectories(ConfigRoot + '\default') then RaiseException('Cannot create default profile');
  finally
    Files.Free;
  end;
end;

procedure ApplyConfiguration;
var
  Files, Created: TStringList;
  Backup, Source, Destination: String;
  I, Suffix: Integer;
  Started: Boolean;
begin
  Files := TStringList.Create;
  Created := TStringList.Create;
  Started := False;
  Backup := '';
  try
    try
      if ResetConfig and DirExists(ConfigRoot) then begin
        CollectConfigs(ConfigRoot, '', Files);
        Backup := ConfigRoot + '\installer-backup\' + GetDateTimeString('yyyymmdd-hhnnss', '-', ':');
        Suffix := 0;
        while DirExists(Backup + '-' + IntToStr(Suffix)) do Suffix := Suffix + 1;
        Backup := Backup + '-' + IntToStr(Suffix);
        for I := 0 to Files.Count - 1 do begin
          Source := ConfigRoot + '\' + Files[I];
          Destination := Backup + '\' + Files[I];
          if not ForceDirectories(ExtractFileDir(Destination)) or not CopyFile(Source, Destination, True) then
            RaiseException('Configuration backup failed; originals have not been changed');
        end;
      end;
      ConfigBackup := Backup;
      Started := True;
      for I := 0 to Files.Count - 1 do
        if not DeleteFile(ConfigRoot + '\' + Files[I]) then RaiseException('Cannot reset configuration');
      WriteChoices(Created);
    except
      if Started then begin
        for I := 0 to Created.Count - 1 do DeleteFile(Created[I]);
        for I := 0 to Files.Count - 1 do
          if not CopyFile(Backup + '\' + Files[I], ConfigRoot + '\' + Files[I], False) then
            Log('Cannot restore configuration; backup retained: ' + Files[I]);
      end;
      RaiseException(GetExceptionMessage);
    end;
  finally
    Created.Free;
    Files.Free;
  end;
end;

procedure WriteMediaReadme(const Folder, Content: String);
var
  Filename: String;
begin
  if IsReparseDirectory(ConfigRoot + '\' + Folder) then begin
    Log('Preserving linked user-media folder without writing a README: ' + Folder);
    Exit;
  end;
  Filename := ConfigRoot + '\' + Folder + '\README.txt';
  if not FileExists(Filename) then
    if not SaveStringToFile(Filename, Content + #13#10, False) then RaiseException('Cannot write user media README');
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep <> ssPostInstall then Exit;
  VerifyInstalledPayload;
  if not PreserveProfile then ApplyConfiguration;
  WriteMediaReadme('SixthSense', 'Custom Sixth Sense icon: SixthSenseIcon.png. Select it in the Driftkings settings panel. This folder is never removed by the uninstaller.');
  WriteMediaReadme('images', 'Custom overlay images: use mods/configs/driftkings/images/<filename>.png in the settings panel. This folder is never removed by the uninstaller.');
end;
