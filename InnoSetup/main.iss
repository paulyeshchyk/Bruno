; Inno Setup Script for Bruno Clicker (--onedir версия)

[Setup]
AppId={{B7A3E2C1-4D5F-4A6B-9C8D-E0F1A2B3C4D5}
AppName=Bruno Clicker
AppVersion=1.03
DefaultDirName={pf}\BrunoClicker
DefaultGroupName=Bruno Clicker
UninstallDisplayIcon={app}\bruno_clicker.exe
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=admin
OutputBaseFilename=BrunoClickerSetup
AppModifyPath="""{app}\unins000.exe"" /modify=1"
CloseApplications=yes

[UninstallDelete]
Type: filesandordirs; Name: "{app}\_internal"
Type: filesandordirs; Name: "{app}"

[Files]
Source: "..\dist\BrunoSuite\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs

[Registry]
; Протокол (уже есть)
Root: HKCR; Subkey: "brunogs"; ValueType: string; ValueName: ""; ValueData: "URL:Bruno GS Protocol"; Flags: uninsdeletekey
Root: HKCR; Subkey: "brunogs"; ValueType: string; ValueName: "URL Protocol"; ValueData: ""
Root: HKCR; Subkey: "brunogs\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\bruno_clicker.exe"" ""%1"""

; Контекстное меню для .yml
Root: HKCR; Subkey: "SystemFileAssociations\.yml\shell\CopyBrunoLink"; ValueType: string; ValueName: ""; ValueData: "Копировать Bruno-ссылку"; Flags: uninsdeletekey
Root: HKCR; Subkey: "SystemFileAssociations\.yml\shell\CopyBrunoLink"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\bruno_generator.exe"
Root: HKCR; Subkey: "SystemFileAssociations\.yml\shell\CopyBrunoLink\command"; ValueType: string; ValueName: ""; ValueData: """{app}\bruno_generator.exe"" ""%1"""

[InstallDelete]
Type: filesandordirs; Name: "{app}\_internal"

[InitializeSetup]
Exec(UninstallStr, '/VERYSILENT /NORESTART /SUPPRESSMSGBOXES', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);

[Code]
var
  BrunoPathPage: TInputDirWizardPage;

function GetUninstallString(): String;
var
  sKey: String;
begin
  Result := '';
  sKey := 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{B7A3E2C1-4D5F-4A6B-9C8D-E0F1A2B3C4D5}_is1';
  
  // Ищем везде, где это возможно
  if not RegQueryStringValue(HKLM, sKey, 'UninstallString', Result) then
    if not RegQueryStringValue(HKCU, sKey, 'UninstallString', Result) then
      // На всякий случай проверяем 64-битную ветку явно
      if not RegQueryStringValue(HKLM64, sKey, 'UninstallString', Result) then
        RegQueryStringValue(HKCU64, sKey, 'UninstallString', Result);
end;

function IsAlreadyInstalled(): Boolean;
begin
  Result := GetUninstallString() <> '';
end;

function InitializeSetup(): Boolean;
var
  V: Integer;
  UninstallStr: String;
  ResultCode: Integer;
begin
  Result := True;
  UninstallStr := GetUninstallString();

  if UninstallStr <> '' then
  begin
    V := MsgBox('Bruno Clicker уже установлен.' + #13#10#13#10 +
                'Нажав (Да) Вы ОБНОВИТЕ программу' + #13#10 +
                'Нажав (Нет) Вы сначала удалите старую версию,' + #13#10 +
                'а затем установите новую.', 
                mbConfirmation, MB_YESNOCANCEL);
    
    if V = IDYES then
    begin
      Result := True;
    end
    else if V = IDNO then
    begin
      // Очищаем путь от кавычек для корректного запуска
      StringChangeEx(UninstallStr, '"', '', True);
      
      // Запускаем старый деинсталлятор в тихом режиме
      if Exec(UninstallStr, '/VERYSILENT /SUPPRESSMSGBOXES', '', SW_SHOW, ewWaitUntilTerminated, ResultCode) then
      begin
        MsgBox('Старая версия удалена. Теперь будет выполнена чистая установка.', mbInformation, MB_OK);
        Result := True;
      end;
    end
    else
      Result := False;
  end;
end;

function FindBrunoPath(): string;
var
  S: string;
begin
  Result := '';
  if RegQueryStringValue(HKLM, 'SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\Bruno.exe', '', S) then
    Result := ExtractFilePath(S)
  else if RegQueryStringValue(HKCU, 'SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\Bruno.exe', '', S) then
    Result := ExtractFilePath(S)
  else if FileExists(ExpandConstant('{localappdata}\Programs\Bruno\Bruno.exe')) then
    Result := ExpandConstant('{localappdata}\Programs\Bruno')
  else if FileExists(ExpandConstant('{commonpf}\Bruno\Bruno.exe')) then
    Result := ExpandConstant('{commonpf}\Bruno')
  else
    Result := 'C:\Program Files\Bruno';
end;

procedure InitializeWizard;
var
  DetectedPath: string;
begin
  DetectedPath := FindBrunoPath();
  BrunoPathPage := CreateInputDirPage(wpSelectDir, 'Выбор папки Bruno', 'Где установлен оригинал?', '', False, '');
  BrunoPathPage.Add('');
  BrunoPathPage.Values[0] := DetectedPath;
end;