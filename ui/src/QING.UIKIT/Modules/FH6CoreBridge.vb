Imports System.Diagnostics
Imports System.Text.Json
Imports System.Text.Json.Serialization

Public Class FH6AutoConfig
    <JsonPropertyName("race_count")>
    Public Property RaceCount As Integer = 99

    <JsonPropertyName("buy_count")>
    Public Property BuyCount As Integer = 30

    <JsonPropertyName("cj_count")>
    Public Property CjCount As Integer = 30

    <JsonPropertyName("sc_count")>
    Public Property ScCount As Integer = 30

    <JsonPropertyName("chk_1")>
    Public Property Chk1 As Boolean = True

    <JsonPropertyName("chk_2")>
    Public Property Chk2 As Boolean = True

    <JsonPropertyName("chk_3")>
    Public Property Chk3 As Boolean = True

    <JsonPropertyName("chk_4")>
    Public Property Chk4 As Boolean = True

    <JsonPropertyName("next_1")>
    Public Property Next1 As Integer = 2

    <JsonPropertyName("next_2")>
    Public Property Next2 As Integer = 3

    <JsonPropertyName("next_3")>
    Public Property Next3 As Integer = 4

    <JsonPropertyName("next_4")>
    Public Property Next4 As Integer = 1

    <JsonPropertyName("global_loops")>
    Public Property GlobalLoops As Integer = 10

    <JsonPropertyName("skill_dirs")>
    Public Property SkillDirs As List(Of String) = New List(Of String) From {"right", "up", "up", "up", "left"}

    <JsonPropertyName("share_code")>
    Public Property ShareCode As String = "890169683"

    <JsonPropertyName("auto_restart")>
    Public Property AutoRestart As Boolean = False

    <JsonPropertyName("restart_cmd")>
    Public Property RestartCommand As String = "start steam://run/2483190"

    <JsonPropertyName("sell_mode")>
    Public Property SellMode As Integer = 1

    <JsonPropertyName("use_ocr")>
    Public Property UseOcr As Boolean = False

    <JsonPropertyName("ocr_lang")>
    Public Property OcrLang As String = "简体中文"

    <JsonPropertyName("calc_a")>
    Public Property CalcA As String = ""

    <JsonPropertyName("calc_b")>
    Public Property CalcB As String = "81700"

    <JsonPropertyName("calc_c")>
    Public Property CalcC As String = "30"

    <JsonPropertyName("start_hotkey")>
    Public Property StartHotkey As String = "F7"

    <JsonPropertyName("stop_hotkey")>
    Public Property StopHotkey As String = "F8"

    <JsonPropertyName("hotkey_start_task")>
    Public Property HotkeyStartTask As String = "race"
End Class

Public Class FH6CoreBridge
    Public Event LogReceived(line As String)
    Public Event StateChanged(isRunning As Boolean)

    Public Sub PublishLog(line As String)
        RaiseEvent LogReceived(line)
    End Sub

    Private _process As Process
    Private ReadOnly _jsonOptions As New JsonSerializerOptions With {
        .WriteIndented = True,
        .Encoder = Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping
    }

    Public ReadOnly Property ProjectRoot As String
        Get
            Dim baseDir = Path.GetFullPath(AppContext.BaseDirectory)
            If File.Exists(Path.Combine(baseDir, "FH6AutoCore.exe")) OrElse
               File.Exists(Path.Combine(baseDir, "config.json")) Then
                Return baseDir
            End If

            Dim dir = New DirectoryInfo(AppContext.BaseDirectory)
            Do While dir IsNot Nothing
                If File.Exists(Path.Combine(dir.FullName, "main.py")) Then Return dir.FullName
                dir = dir.Parent
            Loop

            Dim fallback = Path.GetFullPath(Path.Combine(AppContext.BaseDirectory, "..\..\..\..\..\..\"))
            Return fallback
        End Get
    End Property

    Public ReadOnly Property ConfigPath As String
        Get
            Return Path.Combine(ProjectRoot, "config.json")
        End Get
    End Property

    Public ReadOnly Property CoreExePath As String
        Get
            Return Path.Combine(ProjectRoot, "FH6AutoCore.exe")
        End Get
    End Property

    Public ReadOnly Property CoreEntryPath As String
        Get
            Return Path.Combine(ProjectRoot, "fh6auto_core", "headless.py")
        End Get
    End Property

    Public ReadOnly Property LaunchMode As String
        Get
            If File.Exists(CoreExePath) Then Return "Bundled core exe"
            If File.Exists(CoreEntryPath) AndAlso CommandExists("python.exe") Then Return "Python module fallback"
            If File.Exists(CoreEntryPath) Then Return "Python launcher fallback"
            Return "Missing core"
        End Get
    End Property

    Public ReadOnly Property IsRunning As Boolean
        Get
            Return _process IsNot Nothing AndAlso Not _process.HasExited
        End Get
    End Property

    Public Function LoadConfig() As FH6AutoConfig
        Try
            If File.Exists(ConfigPath) Then
                Dim text = File.ReadAllText(ConfigPath, Encoding.UTF8)
                Dim cfg = JsonSerializer.Deserialize(Of FH6AutoConfig)(text)
                If cfg IsNot Nothing Then Return cfg
            End If
        Catch ex As Exception
            RaiseEvent LogReceived("配置文件读取失败，已回退到默认值：" & ex.Message)
        End Try
        Return New FH6AutoConfig()
    End Function

    Public Sub SaveConfig(config As FH6AutoConfig)
        Directory.CreateDirectory(ProjectRoot)
        Dim text = JsonSerializer.Serialize(config, _jsonOptions)
        File.WriteAllText(ConfigPath, text, Encoding.UTF8)
        RaiseEvent LogReceived("配置已保存：" & ConfigPath)
    End Sub

    Public Sub StartTask(stepName As String)
        If IsRunning Then
            RaiseEvent LogReceived("任务已在运行。")
            Return
        End If

        Dim coreExe = CoreExePath
        Dim coreEntry = CoreEntryPath
        If Not File.Exists(coreExe) AndAlso Not File.Exists(coreEntry) Then
            RaiseEvent LogReceived("未找到任务执行入口：" & coreEntry)
            Return
        End If

        Dim fileName As String
        Dim arguments As String
        Dim launchKind As String
        If File.Exists(coreExe) Then
            fileName = coreExe
            arguments = $"--start {stepName}"
            launchKind = "FH6AutoCore.exe"
        ElseIf CommandExists("python.exe") Then
            fileName = "python"
            arguments = $"-u -m fh6auto_core.headless --start {stepName}"
            launchKind = "python -m fh6auto_core.headless"
        Else
            fileName = "py"
            arguments = $"-3 -u -m fh6auto_core.headless --start {stepName}"
            launchKind = "py -3 -m fh6auto_core.headless"
        End If

        Dim psi As New ProcessStartInfo With {
            .FileName = fileName,
            .Arguments = arguments,
            .WorkingDirectory = ProjectRoot,
            .UseShellExecute = False,
            .CreateNoWindow = True,
            .RedirectStandardOutput = True,
            .RedirectStandardError = True,
            .StandardOutputEncoding = Encoding.UTF8,
            .StandardErrorEncoding = Encoding.UTF8
        }

        _process = New Process With {.StartInfo = psi, .EnableRaisingEvents = True}
        AddHandler _process.OutputDataReceived, Sub(senderObj, e)
                                                    If e.Data IsNot Nothing Then RaiseEvent LogReceived(e.Data)
                                                End Sub
        AddHandler _process.ErrorDataReceived, Sub(senderObj, e)
                                                   If e.Data IsNot Nothing Then RaiseEvent LogReceived("[stderr] " & e.Data)
                                               End Sub
        AddHandler _process.Exited, Sub()
                                        RaiseEvent LogReceived("任务进程已退出。")
                                        RaiseEvent StateChanged(False)
                                    End Sub

        Try
            _process.Start()
            _process.BeginOutputReadLine()
            _process.BeginErrorReadLine()
            RaiseEvent LogReceived($"已开始任务：{stepName} ({launchKind})")
            RaiseEvent StateChanged(True)
        Catch ex As Exception
            RaiseEvent LogReceived("开始任务失败：" & ex.Message)
            RaiseEvent StateChanged(False)
        End Try
    End Sub

    Public Sub StopTask()
        If Not IsRunning Then
            RaiseEvent LogReceived("当前没有正在运行的任务。")
            RaiseEvent StateChanged(False)
            Return
        End If

        Try
            _process.Kill(True)
            RaiseEvent LogReceived("已停止任务。")
        Catch ex As Exception
            RaiseEvent LogReceived("停止任务失败：" & ex.Message)
        Finally
            RaiseEvent StateChanged(False)
        End Try
    End Sub

    Private Function CommandExists(commandName As String) As Boolean
        Dim pathValue = Environment.GetEnvironmentVariable("PATH")
        If String.IsNullOrWhiteSpace(pathValue) Then Return False

        For Each folder In pathValue.Split(";"c)
            If String.IsNullOrWhiteSpace(folder) Then Continue For
            Try
                If File.Exists(Path.Combine(folder.Trim(), commandName)) Then Return True
            Catch
            End Try
        Next

        Return False
    End Function
End Class
