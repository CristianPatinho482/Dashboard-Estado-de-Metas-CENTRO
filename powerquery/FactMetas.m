let
    Ruta = RutaCurados & "\metas",
    Archivos = try Folder.Files(Ruta) otherwise #table({"Content", "Name", "Extension"}, {}),
    Csvs = Table.SelectRows(Archivos, each Text.Lower([Extension]) = ".csv"),
    Columnas = {"IdPeriodo", "IdCentro", "IdCategoria", "IdNivelFormacion", "IdEstrategia", "Indicador", "Indicador_Normalizado", "Meta", "Ejecucion", "OrigenArchivo", "Hoja", "DiaCorte"},
    Esquema = type table [
        IdPeriodo = number, IdCentro = number, IdCategoria = number, IdNivelFormacion = number,
        IdEstrategia = number, Indicador = text, Indicador_Normalizado = text, Meta = number,
        Ejecucion = number, OrigenArchivo = text, Hoja = text, DiaCorte = number
    ],
    Tablas = List.Transform(Table.ToRecords(Csvs), each
        let
            t = Table.PromoteHeaders(Csv.Document([Content], [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv])),
            tipado = Table.TransformColumnTypes(t, {
                {"IdPeriodo", Int64.Type}, {"IdCentro", Int64.Type}, {"IdCategoria", Int64.Type},
                {"IdNivelFormacion", Int64.Type}, {"IdEstrategia", Int64.Type},
                {"Meta", Int64.Type}, {"Ejecucion", Int64.Type}, {"DiaCorte", Int64.Type}
            })
        in
            Table.SelectColumns(tipado, Columnas)),
    Final = if List.IsEmpty(Tablas) then #table(Esquema, {}) else Table.Combine(Tablas)
in
    Table.Buffer(Final)