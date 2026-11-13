let
    Ruta = RutaCurados & "\pe04",
    Archivos = try Folder.Files(Ruta) otherwise #table({"Content", "Name", "Extension"}, {}),
    Csvs = Table.SelectRows(Archivos, each Text.Lower([Extension]) = ".csv"),
    Columnas = {"ID_REGISTRO_UUID", "ID_PERIODO", "CODIGO_FICHA", "NOMBRE_PROGRAMA", "CODIGO_JORNADA", "NOMBRE_JORNADA", "MODALIDAD_FORMACION", "ESTADO_CURSO", "NIVEL_FORMACION", "APRENDICES_MATRICULADOS", "APRENDICES_ACTIVOS", "APRENDICES_CANCELADOS", "TOTAL_HORAS", "IdCentro", "ORIGEN_ARCHIVO"},
    Esquema = type table [
        ID_REGISTRO_UUID = text, ID_PERIODO = number, CODIGO_FICHA = number, NOMBRE_PROGRAMA = text,
        CODIGO_JORNADA = number, NOMBRE_JORNADA = text, MODALIDAD_FORMACION = text, ESTADO_CURSO = text,
        NIVEL_FORMACION = text, APRENDICES_MATRICULADOS = number, APRENDICES_ACTIVOS = number,
        APRENDICES_CANCELADOS = number, TOTAL_HORAS = number, IdCentro = number, ORIGEN_ARCHIVO = text
    ],
    Tablas = List.Transform(Table.ToRecords(Csvs), each
        let
            t = Table.PromoteHeaders(Csv.Document([Content], [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv])),
            horas = Table.TransformColumns(t, {{"TOTAL_HORAS", each try Number.FromText(Text.From(_), "en-US") otherwise 0, type number}}),
            tipado = Table.TransformColumnTypes(horas, {
                {"ID_PERIODO", Int64.Type}, {"CODIGO_FICHA", Int64.Type}, {"CODIGO_JORNADA", Int64.Type},
                {"APRENDICES_MATRICULADOS", Int64.Type}, {"APRENDICES_ACTIVOS", Int64.Type},
                {"APRENDICES_CANCELADOS", Int64.Type}, {"TOTAL_HORAS", type number}, {"IdCentro", Int64.Type}
            })
        in
            Table.SelectColumns(tipado, Columnas)),
    Final = if List.IsEmpty(Tablas) then #table(Esquema, {}) else Table.Combine(Tablas),
    Unicos = Table.Distinct(Final, {"ID_REGISTRO_UUID"})
in
    Table.Buffer(Unicos)