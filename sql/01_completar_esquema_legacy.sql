/*
Correcciones aditivas para los objetos del script original.
No elimina tablas ni datos. El código Django usa sus migraciones para las tablas
Categoria, Maquinaria, Unidad y las tablas internas de autenticación.

Correcciones principales:
- dbo.Equipo se normaliza a dbo.Maquinaria.
- Parametro y AlquilerDetalle se crean antes de funciones, vistas y procedimientos.
- Las relaciones reciben nombres estables.
*/
USE [AlquilerEquipos];
GO
SET XACT_ABORT ON;
SET NOCOUNT ON;
GO

IF OBJECT_ID(N'dbo.Parametro', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Parametro (
        Clave varchar(50) NOT NULL CONSTRAINT PK_Parametro PRIMARY KEY,
        Valor decimal(18,4) NOT NULL,
        CONSTRAINT CK_Parametro_NoNegativo CHECK (Valor >= 0)
    );
END;
GO

IF OBJECT_ID(N'dbo.AlquilerDetalle', N'U') IS NULL
BEGIN
    IF OBJECT_ID(N'dbo.Alquiler', N'U') IS NULL
       OR OBJECT_ID(N'dbo.Unidad', N'U') IS NULL
        THROW 51000, 'Deben existir Alquiler y Unidad antes de AlquilerDetalle.', 1;

    CREATE TABLE dbo.AlquilerDetalle (
        AlquilerDetalleID int IDENTITY(1,1) NOT NULL
            CONSTRAINT PK_AlquilerDetalle PRIMARY KEY,
        AlquilerID int NOT NULL,
        UnidadID int NOT NULL,
        Dias int NOT NULL,
        Subtotal decimal(18,2) NOT NULL,
        Deposito decimal(18,2) NOT NULL,
        EstadoDevolucion varchar(20) NOT NULL
            CONSTRAINT DF_AlquilerDetalle_Estado DEFAULT ('Pendiente'),
        CostoDano decimal(18,2) NOT NULL
            CONSTRAINT DF_AlquilerDetalle_CostoDano DEFAULT (0),
        CONSTRAINT UQ_AlquilerDetalle_Alquiler_Unidad
            UNIQUE (AlquilerID, UnidadID),
        CONSTRAINT FK_AlquilerDetalle_Alquiler FOREIGN KEY (AlquilerID)
            REFERENCES dbo.Alquiler (AlquilerID),
        CONSTRAINT FK_AlquilerDetalle_Unidad FOREIGN KEY (UnidadID)
            REFERENCES dbo.Unidad (UnidadID),
        CONSTRAINT CK_AlquilerDetalle_Dias CHECK (Dias > 0),
        CONSTRAINT CK_AlquilerDetalle_Montos CHECK (Subtotal >= 0 AND Deposito >= 0 AND CostoDano >= 0),
        CONSTRAINT CK_AlquilerDetalle_Estado CHECK (EstadoDevolucion IN ('Pendiente', 'Devuelta', 'Danada'))
    );
END;
GO

CREATE OR ALTER FUNCTION dbo.fn_CalcularTarifa
(
    @EquipoID int,
    @Dias int
)
RETURNS decimal(18,2)
AS
BEGIN
    DECLARE @Dia decimal(18,2), @Sem decimal(18,2), @Mes decimal(18,2);
    SELECT @Dia = TarifaDiaria, @Sem = TarifaSemanal, @Mes = TarifaMensual
    FROM dbo.Maquinaria
    WHERE EquipoID = @EquipoID;

    RETURN (@Dias / 30) * @Mes
         + ((@Dias % 30) / 7) * @Sem
         + ((@Dias % 30) % 7) * @Dia;
END;
GO

CREATE OR ALTER FUNCTION dbo.fn_UnidadDisponible
(
    @UnidadID int,
    @Desde date,
    @Hasta date
)
RETURNS bit
AS
BEGIN
    RETURN CASE
        WHEN EXISTS (
            SELECT 1 FROM dbo.Unidad
            WHERE UnidadID = @UnidadID AND Activo = 1
              AND Estado IN ('Disponible', 'Alquilado')
        )
        AND NOT EXISTS (
            SELECT 1
            FROM dbo.AlquilerDetalle AS d
            JOIN dbo.Alquiler AS a ON a.AlquilerID = d.AlquilerID
            WHERE d.UnidadID = @UnidadID
              AND a.Estado IN ('Reservado', 'Activo')
              AND a.FechaInicio <= @Hasta
              AND a.FechaFinPrevista >= @Desde
        ) THEN 1 ELSE 0 END;
END;
GO

CREATE OR ALTER VIEW dbo.vw_DisponibilidadEquipo
AS
SELECT m.EquipoID, m.Codigo, m.Nombre,
       COUNT(u.UnidadID) AS TotalUnidades,
       SUM(CASE WHEN u.Estado = 'Disponible' THEN 1 ELSE 0 END) AS Disponibles,
       SUM(CASE WHEN u.Estado = 'Alquilado' THEN 1 ELSE 0 END) AS Alquiladas,
       SUM(CASE WHEN u.Estado = 'Mantenimiento' THEN 1 ELSE 0 END) AS EnMantenimiento
FROM dbo.Maquinaria AS m
LEFT JOIN dbo.Unidad AS u
  ON u.EquipoID = m.EquipoID AND u.Estado <> 'Baja' AND u.Activo = 1
GROUP BY m.EquipoID, m.Codigo, m.Nombre;
GO

CREATE OR ALTER VIEW dbo.vw_RentabilidadEquipo
AS
SELECT m.EquipoID, m.Nombre,
       uc.Unidades,
       ISNULL(i.Ingresos, 0) AS Ingresos,
       ISNULL(mm.CostoMant, 0) AS CostoMantenimiento,
       m.CostoAdquisicion * uc.Unidades AS InversionTotal,
       CAST(CASE WHEN m.CostoAdquisicion * uc.Unidades = 0 THEN 0
                 ELSE (ISNULL(i.Ingresos, 0) - ISNULL(mm.CostoMant, 0)) * 100.0
                      / (m.CostoAdquisicion * uc.Unidades)
            END AS decimal(10,2)) AS PorcRetorno
FROM dbo.Maquinaria AS m
CROSS APPLY (
    SELECT COUNT(*) AS Unidades FROM dbo.Unidad WHERE EquipoID = m.EquipoID
) AS uc
OUTER APPLY (
    SELECT SUM(d.Subtotal) AS Ingresos
    FROM dbo.AlquilerDetalle AS d
    JOIN dbo.Unidad AS u ON u.UnidadID = d.UnidadID
    JOIN dbo.Alquiler AS a ON a.AlquilerID = d.AlquilerID
    WHERE u.EquipoID = m.EquipoID AND a.Estado IN ('Activo', 'Finalizado')
) AS i
OUTER APPLY (
    SELECT SUM(mt.Costo) AS CostoMant
    FROM dbo.Mantenimiento AS mt
    JOIN dbo.Unidad AS u ON u.UnidadID = mt.UnidadID
    WHERE u.EquipoID = m.EquipoID
) AS mm;
GO
