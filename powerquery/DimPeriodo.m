let
    AnioSeguro = if AnioPorDefecto = null then 2026 else AnioPorDefecto,
    AniosHechos = List.Select(List.Combine({
        List.Transform(FactMetas[IdPeriodo], each Number.IntegerDivide(_, 100)),
        List.Transform(Fact_PE04_Fichas[ID_PERIODO], each Number.IntegerDivide(_, 100)),
        List.Transform(Fact_PE14_Aprendices[ID_PERIODO], each Number.IntegerDivide(_, 100))
    }), each _ <> null and _ >= 2000 and _ <= 2100),
    Anios = List.Distinct(List.Sort(List.Combine({{AnioSeguro}, AniosHechos}))),
    Meses = {1..12},
    Nombres = {"Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"},
    Filas = List.Combine(List.Transform(Anios, (anio) =>
        List.Transform(Meses, (mes) =>
            let
                inicio = #date(anio, mes, 1),
                fin = Date.EndOfMonth(inicio)
            in
                {
                    anio * 100 + mes,
                    anio,
                    mes,
                    Nombres{mes - 1},
                    Number.RoundUp(mes / 3),
                    inicio,
                    fin,
                    Nombres{mes - 1} & " " & Text.From(anio),
                    mes
                }))),
    Esquema = type table [
        IdPeriodo = number, Anio = number, Mes = number, NombreMes = text, Trimestre = number,
        FechaInicio = date, FechaFin = date, PeriodoTexto = text, OrdenAnual = number
    ],
    Tabla = Table.SelectRows(#table(Esquema, Filas), each [IdPeriodo] <> null)
in
    Table.Buffer(Tabla)