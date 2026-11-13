let
    EsquemaBase = type table [
        IdPoblacion = number, NombrePoblacion = text, NombreAmigable = text,
        GrupoPoblacional = text, EsVulnerable = number, EsDesplazamientoViolencia = number, Orden = number
    ],
    RutaBase = RutaCurados & "\dim_poblacion.csv",
    Base = try
        let
            t = Table.PromoteHeaders(Csv.Document(File.Contents(RutaBase), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv])),
            tipado = Table.TransformColumnTypes(t, {
                {"IdPoblacion", Int64.Type}, {"NombrePoblacion", type text}, {"NombreAmigable", type text},
                {"GrupoPoblacional", type text}, {"EsVulnerable", Int64.Type},
                {"EsDesplazamientoViolencia", Int64.Type}, {"Orden", Int64.Type}
            })
        in
            Table.SelectColumns(tipado, {"IdPoblacion", "NombrePoblacion", "NombreAmigable", "GrupoPoblacional", "EsVulnerable", "EsDesplazamientoViolencia", "Orden"})
        otherwise #table(EsquemaBase, {}),
    SinClasificar = #table(EsquemaBase, {{9999, "SIN_CLASIFICAR", "Sin clasificar", "Otras poblaciones", 0, 0, 9999}}),
    Final = Table.Combine({Base, SinClasificar}),
    Ordenado = Table.Sort(Final, {{"Orden", Order.Ascending}, {"NombrePoblacion", Order.Ascending}})
in
    Table.Buffer(Ordenado)