let
    U = ASTIN_Utils,
    Archivos = U[ListarArchivos](RutaPE14),
    Xlsx = Table.SelectRows(Archivos, each List.Contains({".xlsx", ".xlsm", ".xls"}, [Extension])),
    ConHoja = Table.AddColumn(Xlsx, "Hoja", each U[HojaPrincipal]([Content])),
    ConHechos = Table.AddColumn(ConHoja, "Hechos", each U[ParsePE14]([Hoja][Data], [Name], [IdPeriodo])),
    Columnas = {"ID_REGISTRO_UUID", "ID_PERIODO", "IdCentro", "CODIGO_FICHA", "NombrePoblacion", "Cantidad_Aprendices"},
    Expandido = Table.ExpandTableColumn(ConHechos, "Hechos", Columnas),
    Crudos = Table.SelectColumns(Table.SelectRows(Expandido, each [ID_PERIODO] <> null and [CODIGO_FICHA] <> null), Columnas),
    PeriodosCrudos = List.Distinct(Crudos[ID_PERIODO]),
    RutaCur = RutaCurados & "\pe14",
    ArchivosCur = try Table.SelectRows(Folder.Files(RutaCur), each Text.Lower([Extension]) = ".csv") otherwise #table({"Content", "Name", "Extension"}, {}),
    Esquema = type table [ID_REGISTRO_UUID = text, ID_PERIODO = number, IdCentro = number, CODIGO_FICHA = number, NombrePoblacion = text, Cantidad_Aprendices = number],
    Curados = if Table.RowCount(ArchivosCur) = 0 then #table(Esquema, {}) else
        Table.Combine(List.Transform(Table.ToRecords(ArchivosCur), each
            let
                t = Table.PromoteHeaders(Csv.Document([Content], [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv])),
                tipado = Table.TransformColumnTypes(t, {
                    {"ID_PERIODO", Int64.Type}, {"IdCentro", Int64.Type}, {"CODIGO_FICHA", Int64.Type},
                    {"IdPoblacion", Int64.Type}, {"Cantidad_Aprendices", Int64.Type}
                })
            in
                Table.SelectColumns(tipado, {"ID_REGISTRO_UUID", "ID_PERIODO", "IdCentro", "CODIGO_FICHA", "NombrePoblacion", "Cantidad_Aprendices"}))),
    CuradosFallback = Table.SelectRows(Curados, each not List.Contains(PeriodosCrudos, [ID_PERIODO])),
    Base = Table.Combine({Crudos, CuradosFallback}),
    ConDimension = Table.NestedJoin(Base, {"NombrePoblacion"}, DimPoblacion, {"NombrePoblacion"}, "DimPob", JoinKind.LeftOuter),
    ExpandidoDim = Table.ExpandTableColumn(ConDimension, "DimPob", {"IdPoblacion"}, {"IdPoblacionDim"}),
    ConId = Table.AddColumn(ExpandidoDim, "IdPoblacion", each if [IdPoblacionDim] = null then 9999 else [IdPoblacionDim], Int64.Type),
    Final = Table.SelectColumns(ConId, {"ID_REGISTRO_UUID", "ID_PERIODO", "IdCentro", "CODIGO_FICHA", "IdPoblacion", "NombrePoblacion", "Cantidad_Aprendices"}),
    Unicos = Table.Distinct(Final, {"ID_REGISTRO_UUID"}),
    Tipado = Table.TransformColumnTypes(Unicos, {
        {"ID_PERIODO", Int64.Type}, {"IdCentro", Int64.Type}, {"CODIGO_FICHA", Int64.Type},
        {"IdPoblacion", Int64.Type}, {"Cantidad_Aprendices", Int64.Type}
    })
in
    Table.Buffer(Tipado)