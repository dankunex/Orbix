#define MyAppName "Orbix"
#define MyAppVersion "1.5.1"
#define MyAppPublisher "ivandfx"
#define MyAppURL "https://ivandfx.com/labs/orbix"
#define MyAppExeName "orbix.exe"

[Setup]
AppId={{50BF0047-5CA7-4953-8742-4FFE7D22E762}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=E:\Orbix\output
OutputBaseFilename=OrbixSetup
SetupIconFile=E:\Orbix\img\orbix-inst.ico
WizardImageFile=E:\Orbix\img\orbix-large.bmp
WizardSmallImageFile=E:\Orbix\img\orbicon.bmp
SolidCompression=yes
WizardStyle=classic
WizardResizable=yes

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "catalan"; MessagesFile: "compiler:Languages\Catalan.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "E:\Orbix\dist\orbix\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "E:\Orbix\dist\orbix\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; WorkingDir: "{app}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
function DwmSetWindowAttribute(hwnd: HWND; dwAttribute: DWORD; var pvAttribute: DWORD; cbAttribute: DWORD): Longint;
  external 'DwmSetWindowAttribute@dwmapi.dll stdcall delayload';

const
  USE_DARK_MODE = True;

  DARK_BG     = $222222;
  DARK_PURPLE = $CA8DC5;
  DARK_TEXT   = $FFFFFF;
  DARK_MUTED  = $CCCCCC;

  LIGHT_BG     = $F9F9F9;
  LIGHT_PURPLE = $8E3A89;
  LIGHT_TEXT   = $111111;
  LIGHT_MUTED  = $555555;

procedure SetTitleBarMode(Wnd: HWND; EnableDark: Boolean);
var
  DarkMode: DWORD;
begin
  try
    if EnableDark then DarkMode := 1 else DarkMode := 0;
    if DwmSetWindowAttribute(Wnd, 20, DarkMode, 4) <> 0 then
    begin
      DwmSetWindowAttribute(Wnd, 19, DarkMode, 4);
    end;
  except
  end;
end;

procedure ApplyTheme;
var
  BgColor, AccentColor, TextColor, MutedColor: TColor;
begin
  if USE_DARK_MODE then
  begin
    BgColor     := DARK_BG;
    AccentColor := DARK_PURPLE;
    TextColor   := DARK_TEXT;
    MutedColor  := DARK_MUTED;
  end
  else
  begin
    BgColor     := LIGHT_BG;
    AccentColor := LIGHT_PURPLE;
    TextColor   := LIGHT_TEXT;
    MutedColor  := LIGHT_MUTED;
  end;

  WizardForm.Bevel.Visible := False;
  WizardForm.Bevel1.Visible := False;

  WizardForm.Color := BgColor;
  WizardForm.MainPanel.Color := BgColor;
  WizardForm.InnerPage.Color := BgColor;
  WizardForm.WelcomePage.Color := BgColor;
  WizardForm.FinishedPage.Color := BgColor;
  WizardForm.WizardBitmapImage.BackColor := BgColor;

  WizardForm.WizardSmallBitmapImage.Visible := True;
  WizardForm.WizardSmallBitmapImage.BackColor := BgColor;

  WizardForm.WelcomeLabel1.Color := BgColor;
  WizardForm.WelcomeLabel2.Color := BgColor;
  WizardForm.FinishedHeadingLabel.Color := BgColor;
  WizardForm.FinishedLabel.Color := BgColor;

  WizardForm.WelcomeLabel1.Font.Color := AccentColor;
  WizardForm.WelcomeLabel2.Font.Color := TextColor;
  WizardForm.FinishedHeadingLabel.Font.Color := AccentColor;
  WizardForm.FinishedLabel.Font.Color := TextColor;
  WizardForm.RunList.Font.Color := TextColor;

  WizardForm.PageNameLabel.Font.Color := AccentColor;
  WizardForm.PageDescriptionLabel.Font.Color := MutedColor;

  WizardForm.SelectTasksLabel.Font.Color := TextColor;
  WizardForm.TasksList.Color := BgColor;
  WizardForm.TasksList.Font.Color := TextColor;

  WizardForm.SelectDirLabel.Color := BgColor;
  WizardForm.SelectDirLabel.Font.Color := TextColor;
  
  WizardForm.SelectDirBrowseLabel.Color := BgColor;
  WizardForm.SelectDirBrowseLabel.Font.Color := TextColor;

  WizardForm.DirEdit.Color := BgColor;
  WizardForm.DirEdit.Font.Color := AccentColor;

  WizardForm.DiskSpaceLabel.Color := BgColor;
  WizardForm.DiskSpaceLabel.Font.Color := MutedColor;

  WizardForm.ReadyLabel.Font.Color := TextColor;
  WizardForm.FilenameLabel.Font.Color := AccentColor;
  WizardForm.StatusLabel.Font.Color := MutedColor;
end;

procedure InitializeWizard;
begin
  WizardForm.ClientWidth := ScaleX(500);
  WizardForm.ClientHeight := ScaleY(420);

  SetTitleBarMode(WizardForm.Handle, USE_DARK_MODE);
  ApplyTheme;
end;