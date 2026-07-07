Public Class FH6PipelineCalculation
    Public Property TotalCars As Long
    Public Property TotalRaces As Long
    Public Property GlobalLoops As Integer
    Public Property RaceCount As Integer
    Public Property ActionCount As Integer
End Class

Public Module FH6PipelineCalculator
    Public Function Calculate(targetCr As Long, costPerCar As Long, spPerCar As Long) As FH6PipelineCalculation
        If costPerCar <= 0 OrElse spPerCar <= 0 Then
            Throw New ArgumentOutOfRangeException(NameOf(costPerCar), "单车成本或技能点不能为 0。")
        End If

        Dim totalCars = targetCr \ costPerCar
        Dim totalRaces = (totalCars * spPerCar) \ 10

        If totalRaces <= 0 Then
            Throw New InvalidOperationException($"目标金额不足(只够买{totalCars}辆车)，无法产生有效跑图。")
        End If

        Dim finalLoops As Long
        Dim finalRacesPerLoop As Long

        If totalRaces <= 99 Then
            finalLoops = 1
            finalRacesPerLoop = totalRaces
        Else
            Dim loops = CLng(Math.Ceiling(totalRaces / 99.0R))
            Dim avgRaces = totalRaces \ loops

            If avgRaces >= 70 Then
                finalLoops = loops
                finalRacesPerLoop = avgRaces
            Else
                finalRacesPerLoop = 99
                finalLoops = totalRaces \ 99
            End If
        End If

        Dim carsPerLoop = (finalRacesPerLoop * 10) \ spPerCar
        If finalLoops <= 0 Then Throw New InvalidOperationException("计算后可用大循环次数为0。")

        Return New FH6PipelineCalculation With {
            .TotalCars = totalCars,
            .TotalRaces = totalRaces,
            .GlobalLoops = CInt(Math.Min(Integer.MaxValue, finalLoops)),
            .RaceCount = CInt(Math.Min(Integer.MaxValue, finalRacesPerLoop)),
            .ActionCount = CInt(Math.Min(Integer.MaxValue, carsPerLoop))
        }
    End Function
End Module
