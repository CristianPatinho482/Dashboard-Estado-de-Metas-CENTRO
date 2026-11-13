let
    U = ASTIN_Utils,
    Listar = (ruta as text, origen as text) as table =>
        let
            t = try Folder.Files(ruta) otherwise #table({"Content", "Name", "Extension", "Date modified", "Folder Path"}, {}),
            f = Table.SelectRows(t, each not Text.StartsWith([Name], "~$") and List.Contains({".xlsx", ".xlsm", ".xls", ".csv", ".xml"}, Text.Lower([Extension]))),
            a = Table.AddColumn(f, "Origen", each origen, type text),
            b = Table.AddColumn(a, "IdPeriodo", each U[PeriodoDesdeNombre]([Name], AnioPorDefecto), Int64.Type),
            c = Table.AddColumn(b, "TamanoKB", each Number.Round(Binary.Length([Content]) / 1024, 1), type number),
            d = Table.SelectColumns(c, {"Origen", "Name", "Extension", "IdPeriodo", "Date modified", "TamanoKB"})
        in
            d,
    Metas = Listar(RutaMetas, "01_Metas"),
    PE04 = Listar(RutaPE04, "02_Reportes_PE04"),
    PE14 = Listar(RutaPE14, "03_Reportes_PE14"),
    Todos = Table.Combine({Metas, PE04, PE14}),
    Renombrado = Table.RenameColumns(Todos, {{"Name", "Archivo"}, {"Date modified", "FechaModificacion"}}),
    Ordenado = Table.Sort(Renombrado, {{"Origen", Order.Ascending}, {"IdPeriodo", Order.Descending}, {"Archivo", Order.Ascending}})
in
    Table.Buffer(Ordenado)