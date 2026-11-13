let
    Ruta = RutaCurados & "\pe14",
    Archivos = try Folder.Files(Ruta) otherwise #table({"Content", "Name", "Extension"}, {}),
    Csvs = Table.SelectRows(Archivos, each Text.Lower([Extension]) = ".csv"),
    Columnas = {"ID_REGISTRO_UUID", "ID_PERIODO", "IdCentro", "CODIGO_FICHA", "IdPoblacion", "NombrePoblacion", "Cantidad_Aprendices"},
    Esquema = type table [
        ID_REGISTRO_UUID = text, ID_PERIODO = number, IdCentro = number, CODIGO_FICHA = number,
        IdPoblacion = number, NombrePoblacion = text, Cantidad_Aprendices = number
    ],
    Tablas = List.Transform(Table.ToRecords(Csvs), each
        let
            t = Table.PromoteHeaders(Csv.Document([Content], [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv])),
            tipado = Table.TransformColumnTypes(t, {
                {"ID_PERIODO", Int64.Type}, {"IdCentro", Int64.Type}, {"CODIGO_FICHA", Int64.Type},
                {"IdPoblacion", Int64.Type}, {"Cantidad_Aprendices", Int64.Type}
            })
        in
            Table.SelectColumns(tipado, Columnas)),
    Base = if List.IsEmpty(Tablas) then #table(Esquema, {}) else Table.Combine(Tablas),
    ConDimension = Table.NestedJoin(Base, {"NombrePoblacion"}, DimPoblacion, {"NombrePoblacion"}, "DimPob", JoinKind.LeftOuter),
    Expandido = Table.ExpandTableColumn(ConDimension, "DimPob", {"IdPoblacion"}, {"IdPoblacionDim"}),
    ConId = Table.AddColumn(Expandido, "IdPoblacionFinal", each if [IdPoblacionDim] = null then 9999 else [IdPoblacionDim], Int64.Type),
    Final = Table.SelectColumns(ConId, {"ID_REGISTRO_UUID", "ID_PERIODO", "IdCentro", "CODIGO_FICHA", "IdPoblacionFinal", "NombrePoblacion", "Cantidad_Aprendices"}),
    Renombrado = Table.RenameColumns(Final, {{"IdPoblacionFinal", "IdPoblacion"}}),
    Unicos = Table.Distinct(Renombrado, {"ID_REGISTRO_UUID"})
in
    Table.Buffer(Unicos)