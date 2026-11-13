let
    U = ASTIN_Utils,
    Archivos = U[ListarArchivos](RutaPE14),
    Xlsx = Table.SelectRows(Archivos, each List.Contains({".xlsx", ".xlsm", ".xls"}, [Extension])),
    ConHoja = Table.AddColumn(Xlsx, "Hoja", each U[HojaPrincipal]([Content])),
    ConPoblaciones = Table.AddColumn(ConHoja, "Poblaciones", each U[CabecerasPE14]([Hoja][Data])),
    Expandido = Table.ExpandListColumn(ConPoblaciones, "Poblaciones"),
    Renombrado = Table.RenameColumns(Table.SelectColumns(Expandido, {"Poblaciones"}), {{"Poblaciones", "NombrePoblacion"}}),
    Limpio = Table.SelectRows(Table.Distinct(Renombrado), each [NombrePoblacion] <> null and [NombrePoblacion] <> ""),
    RutaCur = RutaCurados & "\pe14",
    ArchivosCur = try Table.SelectRows(Folder.Files(RutaCur), each Text.Lower([Extension]) = ".csv") otherwise #table({"Content", "Name", "Extension"}, {}),
    DeCurados = if Table.RowCount(ArchivosCur) = 0 then #table({"NombrePoblacion"}, {}) else
        Table.Combine(List.Transform(Table.ToRecords(ArchivosCur), each
            let
                t = Table.PromoteHeaders(Csv.Document([Content], [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv])),
                s = Table.SelectColumns(t, {"NombrePoblacion"}),
                d = Table.Distinct(s)
            in
                d)),
    Todos = Table.Distinct(Table.Combine({Limpio, DeCurados})),
    Ordenado = Table.Sort(Todos, {{"NombrePoblacion", Order.Ascending}})
in
    Ordenado