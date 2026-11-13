let
    Origen = #table(
        type table [IdNivelFormacion = number, NombreNivelFormacion = text, IdCategoria = number, Orden = number],
        {
            {1, "Tecn#(00F3)logo", 1, 1},
            {2, "T#(00E9)cnico", 1, 2},
            {3, "Operario", 1, 3},
            {4, "Auxiliar", 1, 4},
            {5, "Formaci#(00F3)n Complementaria", 2, 5},
            {6, "Biling#(00FC)ismo", 2, 6},
            {7, "Formaci#(00F3)n Especial Campesina", 2, 7}
        }
    )
in
    Origen