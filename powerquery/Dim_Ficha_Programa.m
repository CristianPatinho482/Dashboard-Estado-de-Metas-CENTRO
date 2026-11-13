let
    Base = Fact_PE04_Fichas,
    Ordenado = Table.Sort(Base, {{"CODIGO_FICHA", Order.Ascending}, {"ID_PERIODO", Order.Descending}}),
    Unicos = Table.Distinct(Ordenado, {"CODIGO_FICHA"}),
    Seleccion = Table.SelectColumns(Unicos, {
        "CODIGO_FICHA", "NOMBRE_PROGRAMA", "CODIGO_JORNADA", "NOMBRE_JORNADA",
        "MODALIDAD_FORMACION", "NIVEL_FORMACION", "IdCentro", "ID_PERIODO"
    }),
    Renombrado = Table.RenameColumns(Seleccion, {{"ID_PERIODO", "UltimoPeriodo"}}),
    Final = Table.Sort(Renombrado, {{"CODIGO_FICHA", Order.Ascending}})
in
    Table.Buffer(Final)