let
    U = ASTIN_Utils,
    Archivos = U[ListarArchivos](RutaMetas),
    Xlsx = Table.RenameColumns(Table.SelectRows(Archivos, each List.Contains({".xlsx", ".xlsm", ".xls"}, [Extension]) and [IdPeriodo] <> null), {{"IdPeriodo", "PeriodoArchivo"}}),
    ConHoja = Table.AddColumn(Xlsx, "HojaFuente", each U[HojaPrincipal]([Content])),
    ConControl = Table.AddColumn(ConHoja, "Control", each U[ParseControl]([HojaFuente][Data], [Name], [PeriodoArchivo], [HojaFuente][Dia])),
    Columnas = {"IdPeriodo", "Meta_Oficial", "Ejecucion_Oficial", "Fuente", "OrigenArchivo", "Hoja", "DiaCorte"},
    Expandido = Table.ExpandTableColumn(ConControl, "Control", Columnas),
    Crudos = Table.SelectRows(Expandido, each [Meta_Oficial] <> null or [Ejecucion_Oficial] <> null),
    RutaBase = RutaCurados & "\control_metas.csv",
    Curados = try
        let
            t = Table.PromoteHeaders(Csv.Document(File.Contents(RutaBase), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv])),
            tipado = Table.TransformColumnTypes(t, {{"IdPeriodo", Int64.Type}, {"Meta_Oficial", type number}, {"Ejecucion_Oficial", type number}, {"DiaCorte", Int64.Type}})
        in
            Table.SelectColumns(tipado, Columnas)
        otherwise #table(type table [IdPeriodo = number, Meta_Oficial = number, Ejecucion_Oficial = number, Fuente = text, OrigenArchivo = text, Hoja = text, DiaCorte = number], {}),
    PeriodosCrudos = List.Distinct(Crudos[IdPeriodo]),
    Fallback = Table.SelectRows(Curados, each not List.Contains(PeriodosCrudos, [IdPeriodo])),
    Final = Table.Combine({Crudos, Fallback}),
    Ordenado = Table.Sort(Final, {{"IdPeriodo", Order.Ascending}, {"DiaCorte", Order.Descending}}),
    Unicos = Table.Distinct(Ordenado, {"IdPeriodo"})
in
    Table.Buffer(Unicos)