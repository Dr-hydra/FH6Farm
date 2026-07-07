Public Module FH6SkillPath
    Public Const StartCell As Integer = 12
    Private Const GridSize As Integer = 4

    Public Function MoveCell(current As Integer, direction As String) As Integer
        Select Case If(direction, "").Trim().ToLowerInvariant()
            Case "up"
                Return If(current \ GridSize > 0, current - GridSize, -1)
            Case "down"
                Return If(current \ GridSize < GridSize - 1, current + GridSize, -1)
            Case "left"
                Return If(current Mod GridSize > 0, current - 1, -1)
            Case "right"
                Return If(current Mod GridSize < GridSize - 1, current + 1, -1)
            Case Else
                Return -1
        End Select
    End Function

    Public Function DirectionsToCells(directions As IEnumerable(Of String)) As List(Of Integer)
        Dim cells As New List(Of Integer) From {StartCell}
        Dim current = StartCell

        For Each direction In If(directions, Enumerable.Empty(Of String)())
            Dim normalized = If(direction, "").Trim().ToLowerInvariant()
            If Not {"up", "down", "left", "right"}.Contains(normalized) Then Continue For

            Dim nextCell = MoveCell(current, normalized)
            If nextCell < 0 OrElse cells.Contains(nextCell) Then Exit For
            cells.Add(nextCell)
            current = nextCell
        Next

        Return cells
    End Function

    Public Function CellsToDirections(cells As IEnumerable(Of Integer)) As List(Of String)
        Dim cellList = If(cells, Enumerable.Empty(Of Integer)()).ToList()
        Dim result As New List(Of String)
        If cellList.Count <= 1 Then Return result

        For index = 1 To cellList.Count - 1
            Dim previous = cellList(index - 1)
            Dim current = cellList(index)
            Dim rowChange = current \ GridSize - previous \ GridSize
            Dim columnChange = current Mod GridSize - previous Mod GridSize

            If rowChange = -1 AndAlso columnChange = 0 Then
                result.Add("up")
            ElseIf rowChange = 1 AndAlso columnChange = 0 Then
                result.Add("down")
            ElseIf rowChange = 0 AndAlso columnChange = -1 Then
                result.Add("left")
            ElseIf rowChange = 0 AndAlso columnChange = 1 Then
                result.Add("right")
            Else
                Exit For
            End If
        Next

        Return result
    End Function

    Public Function AreAdjacent(first As Integer, second As Integer) As Boolean
        Return Math.Abs(first \ GridSize - second \ GridSize) + Math.Abs(first Mod GridSize - second Mod GridSize) = 1
    End Function

    Public Function DirectionName(direction As String) As String
        Select Case direction
            Case "up"
                Return "上"
            Case "down"
                Return "下"
            Case "left"
                Return "左"
            Case Else
                Return "右"
        End Select
    End Function
End Module
