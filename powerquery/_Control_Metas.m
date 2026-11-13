let
    Ruta = RutaCurados & "\control_metas.csv",
    Origen = try
        let
            t = Table.PromoteHeaders(Csv.Document(File.Contents(Ruta), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv])),
            tipado = Table.TransformColumnTypes(t, {
                {"IdPeriodo", Int64.Type}, {"Meta_Oficial", type number},
                {"Ejecucion_Oficial", type number}, {"DiaCorte", Int64.Type}
            })
        in
            Table.SelectColumns(tipado, {"IdPeriodo", "Meta_Oficial", "Ejecucion_Oficial", "Fuente", "OrigenArchivo", "Hoja", "DiaCorte"})
        otherwise #table(type table [IdPeriodo = number, Meta_Oficial = number, Ejecucion_Oficial = number, Fuente = text, OrigenArchivo = text, Hoja = text, DiaCorte = number], {}),
    Ordenado = Table.Sort(Origen, {{"IdPeriodo", Order.Ascending}, {"DiaCorte", Order.Descending}}),
    Unicos = Table.Distinct(Ordenado, {"IdPeriodo"})
in
    Table.Buffer(Unicos)