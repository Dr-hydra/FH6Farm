Public Enum UiKitDemoPage
    Overview = 0
    Controls = 1
    Layout = 2
    Theme = 3
    About = 4
End Enum

Public Class UiKitShellHost
    Public Property CurrentPage As UiKitDemoPage = UiKitDemoPage.Overview
    Public Property LastPage As UiKitDemoPage = UiKitDemoPage.Overview
End Class

Public Module UiKitShellText
    Public Function GetPageTitle(page As UiKitDemoPage) As String
        Select Case page
            Case UiKitDemoPage.Controls
                Return "流程"
            Case UiKitDemoPage.Layout
                Return "悬浮窗"
            Case UiKitDemoPage.Theme
                Return "设置"
            Case UiKitDemoPage.About
                Return "关于"
            Case Else
                Return "控制台"
        End Select
    End Function
End Module

Public Module UiKitShellNavigation
    Public Function GetActiveScroll(child As Object) As MyScrollViewer
        If child Is Nothing OrElse TypeOf child IsNot MyPageRight Then Return Nothing
        Dim page As MyPageRight = child
        If String.IsNullOrWhiteSpace(page.PanScroll) Then Return Nothing
        Return TryCast(page.FindName(page.PanScroll), MyScrollViewer)
    End Function
End Module

Public Class UiKitReferenceEntry
    Public Property Title As String
    Public Property Summary As String
    Public Property Category As String
End Class

Public Module UiKitReferenceCatalog
    Public ReadOnly Entries As New List(Of UiKitReferenceEntry) From {
        New UiKitReferenceEntry With {.Category = "帮助页", .Title = "搜索与分组列表", .Summary = "从参考项目的帮助页结构整理而来，可用于 FAQ、文档索引和命令面板。"},
        New UiKitReferenceEntry With {.Category = "关于页", .Title = "信息、鸣谢与法律卡片", .Summary = "从关于页版式整理为通用卡片组，适合项目介绍、依赖声明和许可信息。"},
        New UiKitReferenceEntry With {.Category = "设置页", .Title = "参数分组面板", .Summary = "从个性化设置页整理出标题、说明、滑块、单选、复选与按钮组合。"},
        New UiKitReferenceEntry With {.Category = "窗口", .Title = "拖放文件解析", .Summary = "使用 WPF DragDrop 解析文件路径，保留通用入口，不绑定业务处理。"}
    }

    Public Function Search(keyword As String) As IEnumerable(Of UiKitReferenceEntry)
        Dim text = If(keyword, "").Trim()
        If text = "" Then Return Entries
        Return Entries.Where(Function(item) item.Title.Contains(text, StringComparison.OrdinalIgnoreCase) OrElse
                                            item.Summary.Contains(text, StringComparison.OrdinalIgnoreCase) OrElse
                                            item.Category.Contains(text, StringComparison.OrdinalIgnoreCase))
    End Function
End Module

Public Module UiKitFileDropService
    Public Function HasFileDrop(e As DragEventArgs) As Boolean
        Return e IsNot Nothing AndAlso e.Data IsNot Nothing AndAlso e.Data.GetDataPresent(DataFormats.FileDrop)
    End Function

    Public Function GetDroppedFiles(e As DragEventArgs) As List(Of String)
        If Not HasFileDrop(e) Then Return New List(Of String)
        Dim raw = TryCast(e.Data.GetData(DataFormats.FileDrop), String())
        If raw Is Nothing Then Return New List(Of String)
        Return raw.Where(Function(path) Not String.IsNullOrWhiteSpace(path)).ToList()
    End Function
End Module
