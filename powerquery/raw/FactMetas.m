let
    U = ASTIN_Utils,
    Archivos = U[ListarArchivos](RutaMetas),
    Xlsx = Table.RenameColumns(Table.SelectRows(Archivos, each List.Contains({".xlsx", ".xlsm", ".xls"}, [Extension]) and [IdPeriodo] <> null), {{"IdPeriodo", "PeriodoArchivo"}}),
    ConHoja = Table.AddColumn(Xlsx, "HojaFuente", each U[HojaPrincipal]([Content])),
    ConHechos = Table.AddColumn(ConHoja, "Hechos", each U[ParseMetas]([HojaFuente][Data], [Name], [PeriodoArchivo], [HojaFuente][Dia])),
    Columnas = {"IdPeriodo", "IdCentro", "IdCategoria", "IdNivelFormacion", "IdEstrategia", "Indicador", "Indicador_Normalizado", "Meta", "Ejecucion", "OrigenArchivo", "Hoja", "DiaCorte"},
    Expandido = Table.ExpandTableColumn(ConHechos, "Hechos", Columnas),
    Ordenado = Table.Sort(Expandido, {{"IdPeriodo", Order.Ascending}, {"Indicador_Normalizado", Order.Ascending}, {"DiaCorte", Order.Descending}}),
    Unicos = Table.Distinct(Ordenado, {"IdPeriodo", "Indicador_Normalizado"}),
    Crudos = Table.SelectColumns(Unicos, Columnas),
    PeriodosCrudos = List.Distinct(Crudos[IdPeriodo]),
    RutaCur = RutaCurados & "\metas",
    ArchivosCur = try Table.SelectRows(Folder.Files(RutaCur), each Text.Lower([Extension]) = ".csv") otherwise #table({"Content", "Name", "Extension"}, {}),
    Curados = if Table.RowCount(ArchivosCur) = 0 then #table(type table [IdPeriodo = number, IdCentro = number, IdCategoria = number, IdNivelFormacion = number, IdEstrategia = number, Indicador = text, Indicador_Normalizado = text, Meta = number, Ejecucion = number, OrigenArchivo = text, Hoja = text, DiaCorte = number], {}) else
        Table.Combine(List.Transform(Table.ToRecords(ArchivosCur), each
            let
                t = Table.PromoteHeaders(Csv.Document([Content], [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv])),
                tipado = Table.TransformColumnTypes(t, {
                    {"IdPeriodo", Int64.Type}, {"IdCentro", Int64.Type}, {"IdCategoria", Int64.Type},
                    {"IdNivelFormacion", Int64.Type}, {"IdEstrategia", Int64.Type},
                    {"Meta", Int64.Type}, {"Ejecucion", Int64.Type}, {"DiaCorte", Int64.Type}
                })
            in
                tipado)),
    CuradosFallback = Table.SelectRows(Curados, each not List.Contains(PeriodosCrudos, [IdPeriodo])),
    Final = Table.Combine({Crudos, Table.SelectColumns(CuradosFallback, Columnas)}),
    Tipado = Table.TransformColumnTypes(Final, {
        {"IdPeriodo", Int64.Type}, {"IdCentro", Int64.Type}, {"IdCategoria", Int64.Type},
        {"IdNivelFormacion", Int64.Type}, {"IdEstrategia", Int64.Type},
        {"Meta", Int64.Type}, {"Ejecucion", Int64.Type}, {"DiaCorte", Int64.Type}
    })
in
    Table.Buffer(Tipado)