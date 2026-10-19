; ==============================================================================
; SceneryX - Modern Inno Setup Installation Script
; Architecture: Windows 64-bit (x64compatible)
; Lemon Squeezy License Key Validation Integration
; ==============================================================================

#ifndef MyAppName
  #define MyAppName "SceneryX"
#endif

#ifndef MyAppVersion
  #define MyAppVersion "PRO_1.1.1"
#endif

#ifndef ReleaseName
  #define ReleaseName "SceneryX_PRO_1.1.1"
#endif

#define MyAppPublisher "Sidestick Priority"
#define MyAppURL "https://github.com/wildbill75/SceneryX"
#define MyAppExeName "SceneryX.exe"
#define MyAppId "{{8B8A6E3F-7A9B-4D2E-B7C6-9E3F1A2B4C5D}}"

#ifndef SourceDir
  #define SourceDir "D:\SceneryX\build\SceneryX"
#endif

#ifndef OutputDir
  #define OutputDir "D:\SceneryX\build\installer\" + ReleaseName
#endif

#ifndef OutputBaseFilename
  #define OutputBaseFilename ReleaseName + "_Setup"
#endif

[Setup]
; Unique identifier for SceneryX
AppId={#MyAppId}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

; Destination Directories and Architecture
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
ArchitecturesInstallIn64BitMode=x64compatible

; Elevation and Security (Safe Program Files directory handling)
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=commandline
UsedUserAreasWarning=no

; Output Settings (Isolated installer directory)
OutputDir={#OutputDir}
OutputBaseFilename={#OutputBaseFilename}
SetupIconFile=D:\SceneryX\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}

; Compression and Packaging
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern

; License & Visuals
LicenseFile=D:\SceneryX\installer\EULA_License.txt
DisableWelcomePage=yes
DisableDirPage=auto
DisableReadyPage=yes

; Process Management
CloseApplications=yes
CloseApplicationsFilter={#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[CustomMessages]
english.LaunchProgram=Launch SceneryX now
english.CleanUserData=Would you like to remove your user preferences, cache, and scanned scenery index in %APPDATA%\SceneryX?
english.LicenseKeyTitle=Product License Activation
english.LicenseKeySubtitle=Please enter your Gumroad license key to verify and unlock installation.
english.LicenseKeyPrompt=Gumroad License Key:
english.LicenseKeyHelp=You can find your license key in your purchase confirmation email or receipt from Gumroad.
english.LicenseKeyInvalid=Invalid license key!%n%nInstallation cannot continue without a valid Gumroad license key. Please check your purchase confirmation email and try again.
english.LicenseKeyNotFound=The license key you entered was not found on Gumroad.%n%nPlease verify the key from your purchase receipt.
english.LicenseKeyLimitReached=The activation limit for this license key has been reached.%n%nPlease contact support or manage your devices.
english.LicenseKeyRefunded=This license key has been refunded, cancelled, or revoked on Gumroad.
english.AlreadyInstalledPrompt=SceneryX is already installed on your system (detected version: %1).%n%nDo you want to proceed with updating / installing version %2?%n%nAll your custom settings, preferences, and sceneries will be preserved.
english.PatchAvailablePrompt=SceneryX %1 is currently installed.%n%nDo you want to install patch %2 now?
english.DowngradeToLiteBlocked=SceneryX Pro (%1) is already installed on this computer.%n%nInstalling SceneryX Lite (%2) over an active SceneryX Pro installation is blocked to prevent downgrading your unlocked Pro features.

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
; Copy all built application files from the isolated build output folder
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "D:\SceneryX\icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; Post-install launch option to execute SceneryX immediately
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram}"; Flags: nowait postinstall skipifsilent
Filename: "{app}\{#MyAppExeName}"; Flags: nowait skipifnotsilent

[UninstallRun]
; Silent rollback logic on uninstallation: reverts MSFS Content.xml, restores UserCfg.opt, and removes in-game toolbar panel
Filename: "{app}\{#MyAppExeName}"; Parameters: "--restore-defaults"; Flags: runhidden waituntilterminated; RunOnceId: "SceneryX_Rollback"

[UninstallDelete]
; Clean up any residual files created during execution
Type: filesandordirs; Name: "{app}\*"

[Registry]
; Registry footprint tracking & clean removal
Root: HKLM; Subkey: "Software\SceneryX"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"; Flags: uninsdeletekey
Root: HKLM; Subkey: "Software\SceneryX"; ValueType: string; ValueName: "Version"; ValueData: "{#MyAppVersion}"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\SceneryX"; ValueType: string; ValueName: "Installed"; ValueData: "1"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\SceneryX"; ValueType: string; ValueName: "Version"; ValueData: "{#MyAppVersion}"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\SceneryX"; ValueType: string; ValueName: "InstallerLanguage"; ValueData: "{language}"; Flags: uninsdeletekey

[Code]
var
  LicenseKeyPage: TInputQueryWizardPage;
  LicenseKeyIndex: Integer;
  ValidatedLicenseKey: string;
  IsUpgradeOrPatch: Boolean;
  RequiresLicenseKeyForLiteToProUpgrade: Boolean;

// Helper function to check command-line parameters
function HasParam(const Param: string): Boolean;
var
  i: Integer;
begin
  Result := False;
  for i := 1 to ParamCount do
  begin
    if CompareText(ParamStr(i), Param) = 0 then
    begin
      Result := True;
      Exit;
    end;
  end;
end;

// Retrieve parameter value from command line (e.g. /LICENSEKEY=xxx)
function GetParamValue(const ParamName: string): string;
var
  i: Integer;
  Prefix: string;
begin
  Result := '';
  Prefix := '/' + Uppercase(ParamName) + '=';
  for i := 1 to ParamCount do
  begin
    if Pos(Prefix, Uppercase(ParamStr(i))) = 1 then
    begin
      Result := Copy(ParamStr(i), Length(Prefix) + 1, Length(ParamStr(i)));
      Exit;
    end;
  end;
end;

// Validate Gumroad license key with online activation & master test key fallback
function ValidateLicenseKey(const Key: string; var ErrorMsg: string): Boolean;
var
  CleanKey: string;
  WinHttpReq: Variant;
  Url: string;
  PostData: string;
  HttpStatus: Integer;
  ResponseText: string;
begin
  CleanKey := Uppercase(Trim(Key));
  ErrorMsg := '';

  if CleanKey = '' then
  begin
    ErrorMsg := CustomMessage('LicenseKeyInvalid');
    Result := False;
    Exit;
  end;

  // 1. Master permanent test keys that will ALWAYS work offline
  if (CleanKey = 'EXMZEZNQ') or
     (CleanKey = 'SCNX-MASTER-2026-OK') or
     (CleanKey = 'SCENERYX-DEV-TEST-KEY') or
     (CleanKey = '11111111-2222-3333-4444-555555555555') or
     (CleanKey = '00000000-0000-0000-0000-000000000000') then
  begin
    Result := True;
    Exit;
  end;

  // 2. Try online activation via official Gumroad API
  try
    WinHttpReq := CreateOleObject('WinHttp.WinHttpRequest.5.1');
    Url := 'https://api.gumroad.com/v2/licenses/verify';
    WinHttpReq.Open('POST', Url, False);
    WinHttpReq.SetRequestHeader('Accept', 'application/json');
    WinHttpReq.SetRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
    PostData := 'product_id=IFBvOgJBf93MMvBUDofAPQ%3D%3D&license_key=' + Trim(Key) + '&increment_uses_count=true';
    WinHttpReq.Send(PostData);
    HttpStatus := WinHttpReq.Status;
    ResponseText := WinHttpReq.ResponseText;
    Log('DEBUG GUMROAD RESPONSE: ' + IntToStr(HttpStatus) + ' ' + ResponseText);

    if (Pos('"refunded":true', Lowercase(ResponseText)) > 0) or
       (Pos('"chargebacked":true', Lowercase(ResponseText)) > 0) then
    begin
      ErrorMsg := CustomMessage('LicenseKeyRefunded');
      Result := False;
      Exit;
    end
    else if (HttpStatus = 200) and (Pos('"success":true', ResponseText) > 0) then
    begin
      Result := True;
      Exit;
    end
    else
    begin
      ErrorMsg := CustomMessage('LicenseKeyNotFound');
      Result := False;
      Exit;
    end;
  except
    // 3. Fallback if offline/firewall: accept if key matches 36-char UUID format (8-4-4-4-12)
    if (Length(CleanKey) = 36) and (CleanKey[9] = '-') and (CleanKey[14] = '-') and (CleanKey[19] = '-') and (CleanKey[24] = '-') then
    begin
      Result := True;
      Exit;
    end;
    // Gumroad 4x8 format: XXXXXXXX-XXXXXXXX-XXXXXXXX-XXXXXXXX (35 chars)
    if (Length(CleanKey) = 35) and (CleanKey[9] = '-') and (CleanKey[18] = '-') and (CleanKey[27] = '-') then
    begin
      Result := True;
      Exit;
    end;
    // 32-char hex key
    if (Length(CleanKey) = 32) then
    begin
      Result := True;
      Exit;
    end;
    ErrorMsg := CustomMessage('LicenseKeyInvalid');
    Result := False;
  end;
end;

// Initialize custom wizard pages
procedure InitializeWizard();
var
  CmdKey: string;
  ExistingKey: string;
begin
  // Create License Key Entry Page right after EULA page
  LicenseKeyPage := CreateInputQueryPage(
    wpLicense,
    CustomMessage('LicenseKeyTitle'),
    CustomMessage('LicenseKeySubtitle'),
    CustomMessage('LicenseKeyHelp')
  );
  LicenseKeyIndex := LicenseKeyPage.Add(CustomMessage('LicenseKeyPrompt'), False);

  // Auto-detect if a valid license key already exists from a previous installation
  ExistingKey := '';
  RegQueryStringValue(HKEY_LOCAL_MACHINE, 'Software\SceneryX', 'LicenseKey', ExistingKey);
  if ExistingKey = '' then
    RegQueryStringValue(HKEY_CURRENT_USER, 'Software\SceneryX', 'LicenseKey', ExistingKey);

  // Check for pre-seeded command line parameter (/LICENSEKEY=... or /KEY=...)
  CmdKey := GetParamValue('LICENSEKEY');
  if CmdKey = '' then
    CmdKey := GetParamValue('KEY');

  if CmdKey <> '' then
    LicenseKeyPage.Values[LicenseKeyIndex] := CmdKey
  else if (ExistingKey <> '') and (not HasParam('/TESTLICENSE')) then
    LicenseKeyPage.Values[LicenseKeyIndex] := ExistingKey;
end;

// Skip all wizard pages when patching an existing installation for a 100% transparent update
function ShouldSkipPage(PageID: Integer): Boolean;
begin
  Result := False;
  if (Pos('LITE', Uppercase('{#MyAppVersion}')) > 0) and (LicenseKeyPage <> nil) and (PageID = LicenseKeyPage.ID) then
  begin
    Result := True;
    Exit;
  end;
  if IsUpgradeOrPatch then
  begin
    if (LicenseKeyPage <> nil) and (PageID = LicenseKeyPage.ID) and RequiresLicenseKeyForLiteToProUpgrade then
    begin
      Result := False;
      Exit;
    end;
    if (PageID = wpWelcome) or
       (PageID = wpLicense) or
       ((LicenseKeyPage <> nil) and (PageID = LicenseKeyPage.ID)) or
       (PageID = wpSelectDir) or
       (PageID = wpSelectComponents) or
       (PageID = wpSelectProgramGroup) or
       (PageID = wpSelectTasks) or
       (PageID = wpReady) then
    begin
      Result := True;
    end;
  end;
end;

// Validation on "Next" click: strictly prevent continuing if key is invalid
function NextButtonClick(CurPageID: Integer): Boolean;
var
  EnteredKey: string;
  ValidationErr: string;
begin
  Result := True;

  if (Pos('LITE', Uppercase('{#MyAppVersion}')) > 0) then
    Exit;

  if IsUpgradeOrPatch and (not RequiresLicenseKeyForLiteToProUpgrade) then
    Exit;

  if (LicenseKeyPage <> nil) and (CurPageID = LicenseKeyPage.ID) then
  begin
    EnteredKey := Trim(LicenseKeyPage.Values[LicenseKeyIndex]);

    if not ValidateLicenseKey(EnteredKey, ValidationErr) then
    begin
      if ValidationErr = '' then
        ValidationErr := CustomMessage('LicenseKeyInvalid');
      MsgBox(ValidationErr, mbCriticalError, MB_OK);
      Result := False;
      Exit;
    end;

    ValidatedLicenseKey := EnteredKey;
  end;
end;

// Post-installation initialization (License, Directories, Sweet Spot Profiles)
procedure CurStepChanged(CurStep: TSetupStep);
var
  AppDataDir: string;
  LicenseFilePath: string;
  JsonPayload: string;
  ResultCode: Integer;
begin
  if CurStep = ssPostInstall then
  begin
    AppDataDir := ExpandConstant('{userappdata}\SceneryX');
    if not DirExists(AppDataDir) then
      ForceDirectories(AppDataDir);

    // 1. Ensure dedicated user data directories exist in %APPDATA%
    ForceDirectories(AppDataDir + '\benchmarks');
    ForceDirectories(AppDataDir + '\custom_profiles');
    ForceDirectories(AppDataDir + '\crash_reports');

    // 2. Save validated license key post-installation (only if newly validated)
    if ValidatedLicenseKey <> '' then
    begin
      RegWriteStringValue(HKEY_LOCAL_MACHINE, 'Software\SceneryX', 'LicenseKey', ValidatedLicenseKey);
      RegWriteStringValue(HKEY_LOCAL_MACHINE, 'Software\SceneryX', 'LicenseStatus', 'Active');
      RegWriteStringValue(HKEY_CURRENT_USER, 'Software\SceneryX', 'LicenseKey', ValidatedLicenseKey);

      LicenseFilePath := AppDataDir + '\license.json';
      JsonPayload := '{"license_key": "' + ValidatedLicenseKey + '", "status": "active", "provider": "gumroad"}';
      SaveStringToFile(LicenseFilePath, JsonPayload, False);
    end;

    // 3. Only generate default profiles on a brand-new installation (NEVER touch user configs/data on a patch)
    if not IsUpgradeOrPatch then
    begin
      if Pos('LITE', Uppercase('{#MyAppVersion}')) = 0 then
        Exec(ExpandConstant('{app}\{#MyAppExeName}'), '--setup-profiles', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
    end
    else if Pos('LITE', Uppercase('{#MyAppVersion}')) = 0 then
    begin
      RegWriteStringValue(HKEY_CURRENT_USER, 'Software\SceneryX', 'PendingChangelogVersion', '{#MyAppVersion}');
      SaveStringToFile(AppDataDir + '\pending_changelog.json', '{"version": "{#MyAppVersion}"}', False);
    end;
  end;
end;

procedure CurPageChanged(CurPageID: Integer);
begin
  if IsUpgradeOrPatch and (CurPageID = wpFinished) then
  begin
    WizardForm.NextButton.OnClick(WizardForm);
  end;
end;

// Detect existing installation and terminate running SceneryX instances before patching/installing
function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
  PrevVersion: string;
  ExistingLicenseKey: string;
  HasProLicense: Boolean;
  IsPrevLite: Boolean;
  IsCurrentLite: Boolean;
  PromptMsg: string;
begin
  Result := True;
  IsUpgradeOrPatch := False;
  RequiresLicenseKeyForLiteToProUpgrade := False;

  // Check if SceneryX is already installed on this machine
  PrevVersion := '';
  ExistingLicenseKey := '';
  if IsWin64 then
  begin
    RegQueryStringValue(HKEY_LOCAL_MACHINE_64, 'Software\SceneryX', 'Version', PrevVersion);
    if PrevVersion = '' then
      RegQueryStringValue(HKEY_CURRENT_USER_64, 'Software\SceneryX', 'Version', PrevVersion);
    RegQueryStringValue(HKEY_LOCAL_MACHINE_64, 'Software\SceneryX', 'LicenseKey', ExistingLicenseKey);
    if ExistingLicenseKey = '' then
      RegQueryStringValue(HKEY_CURRENT_USER_64, 'Software\SceneryX', 'LicenseKey', ExistingLicenseKey);
  end;
  if PrevVersion = '' then
  begin
    if not RegQueryStringValue(HKEY_LOCAL_MACHINE, 'Software\SceneryX', 'Version', PrevVersion) then
      RegQueryStringValue(HKEY_CURRENT_USER, 'Software\SceneryX', 'Version', PrevVersion);
  end;
  if ExistingLicenseKey = '' then
  begin
    if not RegQueryStringValue(HKEY_LOCAL_MACHINE, 'Software\SceneryX', 'LicenseKey', ExistingLicenseKey) then
      RegQueryStringValue(HKEY_CURRENT_USER, 'Software\SceneryX', 'LicenseKey', ExistingLicenseKey);
  end;

  HasProLicense := (Trim(ExistingLicenseKey) <> '') or FileExists(ExpandConstant('{userappdata}\SceneryX\license.json'));
  IsPrevLite := (PrevVersion <> '') and (Pos('LITE', Uppercase(PrevVersion)) > 0);
  IsCurrentLite := (Pos('LITE', Uppercase('{#MyAppVersion}')) > 0);

  if (not HasParam('/TESTLICENSE')) and
     ((PrevVersion <> '') or
      FileExists(ExpandConstant('{autopf}\{#MyAppName}\{#MyAppExeName}')) or
      FileExists(ExpandConstant('{autopf64}\{#MyAppName}\{#MyAppExeName}')) or
      FileExists(ExpandConstant('{userappdata}\SceneryX\settings.json'))) then
  begin
    // Block downgrading from SceneryX Pro to SceneryX Lite
    if IsCurrentLite and (((PrevVersion <> '') and (not IsPrevLite)) or HasProLicense) then
    begin
      if PrevVersion = '' then
        PrevVersion := 'SceneryX Pro';
      MsgBox(FmtMessage(CustomMessage('DowngradeToLiteBlocked'), [PrevVersion, '{#MyAppVersion}']), mbCriticalError, MB_OK);
      Result := False;
      Exit;
    end;

    // Lite is always a direct full installation (never a patch process)
    if not IsCurrentLite then
    begin
      // Require license key activation when upgrading from SceneryX Lite to SceneryX Pro
      if IsPrevLite and (not HasProLicense) then
      begin
        RequiresLicenseKeyForLiteToProUpgrade := True;
      end;

      if PrevVersion = '' then
        PrevVersion := 'Previous Version';

      if (not HasParam('/AUTOPATCH')) and (not WizardSilent) then
      begin
        PromptMsg := FmtMessage(CustomMessage('PatchAvailablePrompt'), [PrevVersion, '{#MyAppVersion}']);
        if MsgBox(PromptMsg, mbConfirmation, MB_OKCANCEL) <> IDOK then
        begin
          Result := False;
          Exit;
        end;
      end;

      IsUpgradeOrPatch := True;
    end;
  end;

  Exec('taskkill.exe', '/F /IM SceneryX.exe', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
end;

// Terminate running SceneryX instances before uninstallation starts
function InitializeUninstall(): Boolean;
var
  ResultCode: Integer;
begin
  Result := True;
  Exec('taskkill.exe', '/F /IM SceneryX.exe', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
end;

// Post-uninstallation cleanup of user data (%APPDATA%\SceneryX and %LOCALAPPDATA%\SceneryX)
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  AppDataPath: string;
  LocalAppDataPath: string;
  DeleteUserData: Boolean;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    AppDataPath := ExpandConstant('{userappdata}\SceneryX');
    LocalAppDataPath := ExpandConstant('{localappdata}\SceneryX');
    DeleteUserData := False;

    // Check if silent cleanup requested or prompt the user interactively
    if HasParam('/CLEANUSERDATA') or HasParam('--clean-userdata') then
    begin
      DeleteUserData := True;
    end
    else if not UninstallSilent then
    begin
      if DirExists(AppDataPath) or DirExists(LocalAppDataPath) then
      begin
        if MsgBox(CustomMessage('CleanUserData'), mbConfirmation, MB_YESNO) = IDYES then
        begin
          DeleteUserData := True;
        end;
      end;
    end;

    if DeleteUserData then
    begin
      if DirExists(AppDataPath) then
      begin
        DelTree(AppDataPath, True, True, True);
      end;
      if DirExists(LocalAppDataPath) then
      begin
        DelTree(LocalAppDataPath, True, True, True);
      end;
      // Remove lingering registry keys
      RegDeleteKeyIncludingSubkeys(HKCU, 'Software\SceneryX');
      RegDeleteKeyIncludingSubkeys(HKLM, 'Software\SceneryX');
    end;
  end;
end;
