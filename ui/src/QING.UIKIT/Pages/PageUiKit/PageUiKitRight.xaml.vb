Public Class PageUiKitRight
    Private Page As UiKitDemoPage = UiKitDemoPage.Overview
    Private CurrentConfig As FH6AutoConfig
    Private ReadOnly SkillPathCells As New List(Of Integer)
    Private ReadOnly SkillPathButtons As New List(Of Button)

    Public Shared Function Create(page As UiKitDemoPage) As PageUiKitRight
        Dim result As New PageUiKitRight()
        result.Configure(page)
        Return result
    End Function

    Public Sub Configure(page As UiKitDemoPage)
        Me.Page = page
        CardDashboard.Visibility = If(page = UiKitDemoPage.Overview, Visibility.Visible, Visibility.Collapsed)
        CardFlow.Visibility = If(page = UiKitDemoPage.Controls, Visibility.Visible, Visibility.Collapsed)
        CardFlowGuide.Visibility = If(page = UiKitDemoPage.Controls, Visibility.Visible, Visibility.Collapsed)
        CardOverlay.Visibility = If(page = UiKitDemoPage.Layout, Visibility.Visible, Visibility.Collapsed)
        CardSettings.Visibility = If(page = UiKitDemoPage.Theme, Visibility.Visible, Visibility.Collapsed)
        CardAbout.Visibility = If(page = UiKitDemoPage.About, Visibility.Visible, Visibility.Collapsed)

        RefreshStateLabel()
    End Sub

    Private Sub PageUiKitRight_Loaded(sender As Object, e As RoutedEventArgs) Handles Me.Loaded
        AddHandler CoreBridge.LogReceived, AddressOf OnCoreLog
        AddHandler CoreBridge.StateChanged, AddressOf OnCoreStateChanged
        InitializeSkillPathGrid()
        LoadConfigToUi()
        Configure(Page)
    End Sub

    Public Sub ShowDroppedFiles(files As IEnumerable(Of String))
        If files Is Nothing Then Return
        AppendLog("拖放文件：" & String.Join(", ", files.Select(Function(path) IO.Path.GetFileName(path))))
    End Sub

    Private Sub LoadConfigToUi()
        CurrentConfig = CoreBridge.LoadConfig()

        TxtShareCode.Text = CurrentConfig.ShareCode
        TxtRaceCount.Text = CurrentConfig.RaceCount.ToString()
        TxtBuyCount.Text = CurrentConfig.BuyCount.ToString()
        TxtCjCount.Text = CurrentConfig.CjCount.ToString()
        TxtScCount.Text = CurrentConfig.ScCount.ToString()
        Chk1.Checked = CurrentConfig.Chk1
        Chk2.Checked = CurrentConfig.Chk2
        Chk3.Checked = CurrentConfig.Chk3
        Chk4.Checked = CurrentConfig.Chk4
        TxtNext1.Text = CurrentConfig.Next1.ToString()
        TxtNext2.Text = CurrentConfig.Next2.ToString()
        TxtNext3.Text = CurrentConfig.Next3.ToString()
        TxtNext4.Text = CurrentConfig.Next4.ToString()
        TxtGlobalLoops.Text = CurrentConfig.GlobalLoops.ToString()
        LoadSkillPath(CurrentConfig.SkillDirs)
        ChkAutoRestart.Checked = CurrentConfig.AutoRestart
        ChkAutoCloseGame.Checked = CurrentConfig.AutoCloseGame
        ChkAutoShutdown.Checked = CurrentConfig.AutoShutdown
        TxtRestartCmd.Text = CurrentConfig.RestartCommand
        TxtCalcA.Text = CurrentConfig.CalcA
        TxtCalcB.Text = CurrentConfig.CalcB
        TxtCalcC.Text = CurrentConfig.CalcC
        CmbSellMode.SelectedIndex = If(CurrentConfig.SellMode = 2, 1, 0)
        CmbCjMode.SelectedIndex = If(CurrentConfig.CjMode = 2, 1, 0)
        TxtStartHotkey.Text = CurrentConfig.StartHotkey
        TxtStopHotkey.Text = CurrentConfig.StopHotkey
        CmbHotkeyStartTask.SelectedIndex = TaskIndex(CurrentConfig.HotkeyStartTask)
        LabConfigPath.Text = "配置文件：" & CoreBridge.ConfigPath
        LabRuntimeInfo.Text = $"项目目录：{CoreBridge.ProjectRoot}{Environment.NewLine}任务执行：{CoreBridge.LaunchMode}"
    End Sub

    Public Sub ReloadConfig()
        InitializeSkillPathGrid()
        LoadConfigToUi()
    End Sub

    Private Function ReadFlowConfig() As FH6AutoConfig
        Dim cfg = CoreBridge.LoadConfig()
        cfg.ShareCode = OnlyDigits(TxtShareCode.Text, "890169683")
        cfg.RaceCount = ReadInt(TxtRaceCount.Text, 99, 1, 999)
        cfg.BuyCount = ReadInt(TxtBuyCount.Text, 30, 0, 999)
        cfg.CjCount = ReadInt(TxtCjCount.Text, 30, 0, 999)
        cfg.ScCount = ReadInt(TxtScCount.Text, 30, 0, 999)
        cfg.Chk1 = Chk1.Checked
        cfg.Chk2 = Chk2.Checked
        cfg.Chk3 = Chk3.Checked
        cfg.Chk4 = Chk4.Checked
        cfg.Next1 = ReadInt(TxtNext1.Text, 2, 1, 4)
        cfg.Next2 = ReadInt(TxtNext2.Text, 3, 1, 4)
        cfg.Next3 = ReadInt(TxtNext3.Text, 4, 1, 4)
        cfg.Next4 = ReadInt(TxtNext4.Text, 1, 1, 4)
        cfg.GlobalLoops = ReadInt(TxtGlobalLoops.Text, 10, 1, 999)
        cfg.SkillDirs = SkillPathToDirections()
        Return cfg
    End Function

    Private Function ReadSettingsConfig() As FH6AutoConfig
        Dim cfg = CoreBridge.LoadConfig()
        cfg.AutoRestart = ChkAutoRestart.Checked
        cfg.AutoCloseGame = ChkAutoCloseGame.Checked
        cfg.AutoShutdown = ChkAutoShutdown.Checked
        cfg.RestartCommand = If(TxtRestartCmd.Text, "").Trim()
        cfg.SellMode = If(CmbSellMode.SelectedIndex = 1, 2, 1)
        cfg.CjMode = If(CmbCjMode.SelectedIndex = 1, 2, 1)
        cfg.CalcA = If(TxtCalcA.Text, "").Trim()
        cfg.CalcB = If(TxtCalcB.Text, "81700").Trim()
        cfg.CalcC = If(TxtCalcC.Text, "30").Trim()
        cfg.StartHotkey = NormalizeHotkey(TxtStartHotkey.Text, "F7")
        cfg.StopHotkey = NormalizeHotkey(TxtStopHotkey.Text, "F8")
        cfg.HotkeyStartTask = TaskValue(CmbHotkeyStartTask.SelectedIndex)
        Return cfg
    End Function

    Private Function ReadInt(raw As String, fallback As Integer, min As Integer, max As Integer) As Integer
        Dim value As Integer
        If Not Integer.TryParse(OnlyDigits(raw, fallback.ToString()), value) Then value = fallback
        Return Math.Max(min, Math.Min(max, value))
    End Function

    Private Function ReadLong(raw As String, fallback As Long) As Long
        Dim value As Long
        If Not Long.TryParse(OnlyDigits(raw, fallback.ToString()), value) Then value = fallback
        Return value
    End Function

    Private Function OnlyDigits(raw As String, fallback As String) As String
        Dim value = New String(If(raw, "").Where(Function(ch) Char.IsDigit(ch)).ToArray())
        If String.IsNullOrWhiteSpace(value) Then Return fallback
        Return value
    End Function

    Private Sub SaveConfig(config As FH6AutoConfig)
        CurrentConfig = config
        CoreBridge.SaveConfig(CurrentConfig)
        FrmMain?.NotifyConfigSaved(CurrentConfig)
    End Sub

    Public Function CaptureConfigFromUi() As FH6AutoConfig
        Select Case Page
            Case UiKitDemoPage.Controls
                Return ReadFlowConfig()
            Case UiKitDemoPage.Theme
                Return ReadSettingsConfig()
            Case Else
                Return CoreBridge.LoadConfig()
        End Select
    End Function

    Public Function SaveVisibleConfig() As FH6AutoConfig
        Dim config = CaptureConfigFromUi()
        If Page = UiKitDemoPage.Controls OrElse Page = UiKitDemoPage.Theme Then
            SaveConfig(config)
        End If
        Return config
    End Function

    Private Sub StartStep(stepName As String)
        CurrentConfig = SaveVisibleConfig()
        CoreBridge.StartTask(stepName)
    End Sub

    Private Sub BtnStartRace_Click(sender As Object, e As MouseButtonEventArgs)
        StartStep("race")
    End Sub

    Private Sub BtnStartBuy_Click(sender As Object, e As MouseButtonEventArgs)
        StartStep("buy")
    End Sub

    Private Sub BtnStartCj_Click(sender As Object, e As MouseButtonEventArgs)
        StartStep("cj")
    End Sub

    Private Sub BtnStartSell_Click(sender As Object, e As MouseButtonEventArgs)
        StartStep("sell")
    End Sub

    Private Sub BtnStop_Click(sender As Object, e As MouseButtonEventArgs)
        CoreBridge.StopTask()
    End Sub

    Private Sub BtnSaveConfig_Click(sender As Object, e As MouseButtonEventArgs)
        SaveConfig(ReadSettingsConfig())
        Hint("配置已保存。", HintType.Green)
    End Sub

    Private Sub BtnCalculatePipeline_Click(sender As Object, e As MouseButtonEventArgs)
        Dim targetCr = ReadLong(TxtCalcA.Text, 0)
        Dim costPerCar = ReadLong(TxtCalcB.Text, 81700)
        Dim spPerCar = ReadLong(TxtCalcC.Text, 30)

        If targetCr <= 0 Then
            Hint("未输入有效目标 CR。", HintType.Red)
            Return
        End If

        Try
            Dim result = FH6PipelineCalculator.Calculate(targetCr, costPerCar, spPerCar)
            Dim cfg = ReadSettingsConfig()
            cfg.RaceCount = result.RaceCount
            cfg.BuyCount = result.ActionCount
            cfg.CjCount = result.ActionCount
            cfg.ScCount = result.ActionCount
            cfg.GlobalLoops = result.GlobalLoops

            SaveConfig(cfg)
            LoadConfigToUi()
            Hint($"已应用：{result.GlobalLoops} 个大循环，每轮跑图 {result.RaceCount} 次，动作 {result.ActionCount} 辆。", HintType.Green)
        Catch ex As Exception
            Hint(ex.Message, HintType.Red)
        End Try
    End Sub

    Private Sub BtnReloadConfig_Click(sender As Object, e As MouseButtonEventArgs)
        LoadConfigToUi()
        Hint("配置已重新加载。", HintType.Blue)
    End Sub

    Private Sub BtnShowOverlay_Click(sender As Object, e As MouseButtonEventArgs)
        FrmMain?.ShowTaskOverlay()
    End Sub

    Private Sub BtnHideOverlay_Click(sender As Object, e As MouseButtonEventArgs)
        FrmMain?.HideTaskOverlay()
    End Sub

    Private Sub BtnResetSkillPath_Click(sender As Object, e As MouseButtonEventArgs)
        ResetSkillPath()
    End Sub

    Private Sub BtnSaveFlowConfig_Click(sender As Object, e As MouseButtonEventArgs)
        SaveConfig(ReadFlowConfig())
        Hint("流程配置已保存并立即生效。", HintType.Green)
    End Sub

    Private Sub BtnOriginalProject_Click(sender As Object, e As MouseButtonEventArgs)
        OpenWebsite("https://github.com/YOUSTHEONE/FH6Auto")
    End Sub

    Private Sub BtnCurrentProject_Click(sender As Object, e As MouseButtonEventArgs)
        OpenWebsite("https://github.com/Dr-hydra/FH6Farm")
    End Sub

    Private Sub OnCoreLog(line As String)
        Dispatcher.Invoke(Sub()
                              AppendLog(line)
                          End Sub)
    End Sub

    Private Sub OnCoreStateChanged(isRunning As Boolean)
        Dispatcher.Invoke(Sub()
                              RefreshStateLabel()
                          End Sub)
    End Sub

    Private Sub AppendLog(line As String)
        TxtLog.AppendText(line & Environment.NewLine)
        TxtLog.ScrollToEnd()
        RefreshStateLabel()
    End Sub

    Private Sub RefreshStateLabel()
    End Sub

    Private Function NormalizeHotkey(raw As String, fallback As String) As String
        Dim value = If(raw, "").Trim().ToUpperInvariant()
        Return If(value = "", fallback, value)
    End Function

    Private Function TaskIndex(task As String) As Integer
        Select Case task
            Case "buy"
                Return 1
            Case "cj"
                Return 2
            Case "sell"
                Return 3
            Case Else
                Return 0
        End Select
    End Function

    Private Function TaskValue(index As Integer) As String
        Return {"race", "buy", "cj", "sell"}(Math.Max(0, Math.Min(3, index)))
    End Function

    Private Sub InitializeSkillPathGrid()
        If SkillPathButtons.Count > 0 Then Return

        For index = 0 To 15
            Dim button As New Button With {
                .Tag = index,
                .Margin = New Thickness(4),
                .FontSize = 13,
                .FontWeight = FontWeights.SemiBold,
                .Cursor = Cursors.Hand,
                .BorderThickness = New Thickness(2)
            }
            AddHandler button.Click, AddressOf SkillPathCell_Click
            SkillPathButtons.Add(button)
            SkillPathGrid.Children.Add(button)
        Next
        ResetSkillPath()
    End Sub

    Private Sub ResetSkillPath()
        SkillPathCells.Clear()
        SkillPathCells.Add(FH6SkillPath.StartCell)
        RefreshSkillPathGrid()
    End Sub

    Private Sub LoadSkillPath(directions As IEnumerable(Of String))
        SkillPathCells.Clear()
        SkillPathCells.AddRange(FH6SkillPath.DirectionsToCells(directions))
        RefreshSkillPathGrid()
    End Sub

    Private Sub SkillPathCell_Click(sender As Object, e As RoutedEventArgs)
        Dim button = TryCast(sender, Button)
        If button Is Nothing Then Return
        Dim index = CInt(button.Tag)
        If SkillPathCells.Contains(index) OrElse Not FH6SkillPath.AreAdjacent(SkillPathCells.Last(), index) Then Return
        SkillPathCells.Add(index)
        RefreshSkillPathGrid()
    End Sub

    Private Sub RefreshSkillPathGrid()
        If SkillPathButtons.Count = 0 Then Return
        Dim endpoint = SkillPathCells.Last()

        For index = 0 To SkillPathButtons.Count - 1
            Dim button = SkillPathButtons(index)
            Dim stepIndex = SkillPathCells.IndexOf(index)
            If stepIndex >= 0 Then
                button.Content = If(stepIndex = 0, "起", (stepIndex + 1).ToString())
                button.Background = New SolidColorBrush(Color.FromRgb(&H28, &H8B, &HEF))
                button.Foreground = Brushes.White
                button.BorderBrush = New SolidColorBrush(Color.FromRgb(&H16, &H6F, &HC7))
                button.IsEnabled = False
            Else
                button.Content = ""
                button.Background = Brushes.Transparent
                button.Foreground = New SolidColorBrush(Color.FromRgb(&H28, &H8B, &HEF))
                button.BorderBrush = If(FH6SkillPath.AreAdjacent(endpoint, index),
                                        New SolidColorBrush(Color.FromRgb(&H28, &H8B, &HEF)),
                                        New SolidColorBrush(Color.FromRgb(&HC9, &HD1, &HD9)))
                button.IsEnabled = FH6SkillPath.AreAdjacent(endpoint, index)
            End If
        Next

        Dim directions = SkillPathToDirections()
        LabSkillPath.Text = $"已选择 {SkillPathCells.Count} 格" &
            If(directions.Count = 0, "，当前仅包含起点。", $"，方向：{String.Join(" → ", directions.Select(Function(direction) FH6SkillPath.DirectionName(direction)))}")
    End Sub

    Private Function SkillPathToDirections() As List(Of String)
        Return FH6SkillPath.CellsToDirections(SkillPathCells)
    End Function
End Class
