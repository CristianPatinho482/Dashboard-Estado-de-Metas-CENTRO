let
    U = ASTIN_Utils,
    Archivos = U[ListarArchivos](RutaPE04),
    Xlsx = Table.SelectRows(Archivos, each List.Contains({".xlsx", ".xlsm", ".xls"}, [Extension])),
    ConHoja = Table.AddColumn(Xlsx, "Hoja", each U[HojaPrincipal]([Content])),
    ConHechos = Table.AddColumn(ConHoja, "Hechos", each U[ParsePE04]([Hoja][Data], [Name], [IdPeriodo])),
    Columnas = {"ID_REGISTRO_UUID", "ID_PERIODO", "CODIGO_FICHA", "NOMBRE_PROGRAMA", "CODIGO_JORNADA", "NOMBRE_JORNADA", "MODALIDAD_FORMACION", "ESTADO_CURSO", "NIVEL_FORMACION", "APRENDICES_MATRICULADOS", "APRENDICES_ACTIVOS", "APRENDICES_CANCELADOS", "TOTAL_HORAS", "IdCentro", "ORIGEN_ARCHIVO"},
    Expandido = Table.ExpandTableColumn(ConHechos, "Hechos", Columnas),
    Crudos = Table.SelectColumns(Table.SelectRows(Expandido, each [ID_PERIODO] <> null and [CODIGO_FICHA] <> null), Columnas),
    PeriodosCrudos = List.Distinct(Crudos[ID_PERIODO]),
    RutaCur = RutaCurados & "\pe04",
    ArchivosCur = try Table.SelectRows(Folder.Files(RutaCur), each Text.Lower([Extension]) = ".csv") otherwise #table({"Content", "Name", "Extension"}, {}),
    Esquema = type table [
        ID_REGISTRO_UUID = text, ID_PERIODO = number, CODIGO_FICHA = number, NOMBRE_PROGRAMA = text,
        CODIGO_JORNADA = number, NOMBRE_JORNADA = text, MODALIDAD_FORMACION = text, ESTADO_CURSO = text,
        NIVEL_FORMACION = text, APRENDICES_MATRICULADOS = number, APRENDICES_ACTIVOS = number,
        APRENDICES_CANCELADOS = number, TOTAL_HORAS = number, IdCentro = number, ORIGEN_ARCHIVO = text
    ],
    Curados = if Table.RowCount(ArchivosCur) = 0 then #table(Esquema, {}) else
        Table.Combine(List.Transform(Table.ToRecords(ArchivosCur), each
            let
                t = Table.PromoteHeaders(Csv.Document([Content], [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv])),
                tipado = Table.TransformColumnTypes(t, {
                    {"ID_PERIODO", Int64.Type}, {"CODIGO_FICHA", Int64.Type}, {"CODIGO_JORNADA", Int64.Type},
                    {"APRENDICES_MATRICULADOS", Int64.Type}, {"APRENDICES_ACTIVOS", Int64.Type},
                    {"APRENDICES_CANCELADOS", Int64.Type}, {"TOTAL_HORAS", type number}, {"IdCentro", Int64.Type}
                })
            in
                Table.SelectColumns(tipado, Columnas))),
    CuradosFallback = Table.SelectRows(Curados, each not List.Contains(PeriodosCrudos, [ID_PERIODO])),
    Final = Table.Combine({Crudos, CuradosFallback}),
    Unicos = Table.Distinct(Final, {"ID_REGISTRO_UUID"}),
    Tipado = Table.TransformColumnTypes(Unicos, {
        {"ID_PERIODO", Int64.Type}, {"CODIGO_FICHA", Int64.Type}, {"CODIGO_JORNADA", Int64.Type},
        {"APRENDICES_MATRICULADOS", Int64.Type}, {"APRENDICES_ACTIVOS", Int64.Type},
        {"APRENDICES_CANCELADOS", Int64.Type}, {"TOTAL_HORAS", type number}, {"IdCentro", Int64.Type}
    })
in
    Table.Buffer(Tipado)