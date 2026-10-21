/* Derivado del script original; nombres corregidos y ejecución repetible. */
USE [AlquilerEquipos]
GO
IF TYPE_ID(N'dbo.TipoListaUnidades') IS NULL OR TYPE_ID(N'dbo.TipoListaDanos') IS NULL
    THROW 51001, 'Faltan los tipos de tabla TipoListaUnidades o TipoListaDanos.', 1;
GO
/****** Object:  StoredProcedure [dbo].[sp_CancelarAlquiler]    Script Date: 19/10/2026 9:20:04 p. m. ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

-- 4.6 Cancelar cotizacion o reserva
CREATE OR ALTER PROCEDURE [dbo].[sp_CancelarAlquiler] @AlquilerID INT, @Motivo VARCHAR(300) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dbo.Alquiler SET Estado = 'Cancelado', Observaciones = @Motivo
    WHERE AlquilerID = @AlquilerID AND Estado IN ('Cotizado','Reservado');
    IF @@ROWCOUNT = 0 THROW 50011, 'Solo se pueden cancelar alquileres Cotizados o Reservados.', 1;
END;
GO
/****** Object:  StoredProcedure [dbo].[sp_ConfirmarReserva]    Script Date: 19/10/2026 9:20:04 p. m. ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

-- 4.2 Convertir una cotizacion en reserva (revalida disponibilidad)
CREATE OR ALTER PROCEDURE [dbo].[sp_ConfirmarReserva] @AlquilerID INT
AS
BEGIN
    SET NOCOUNT ON; SET XACT_ABORT ON;
    SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;

    DECLARE @Ini DATE, @Fin DATE;
    SELECT @Ini = FechaInicio, @Fin = FechaFinPrevista
    FROM dbo.Alquiler WHERE AlquilerID = @AlquilerID AND Estado = 'Cotizado';
    IF @Ini IS NULL THROW 50004, 'El alquiler no existe o no esta en estado Cotizado.', 1;

    BEGIN TRAN;
    IF EXISTS (SELECT 1 FROM dbo.AlquilerDetalle d
               WHERE d.AlquilerID = @AlquilerID
                 AND dbo.fn_UnidadDisponible(d.UnidadID, @Ini, @Fin) = 0)
        THROW 50003, 'Una o mas unidades ya no estan disponibles.', 1;
    UPDATE dbo.Alquiler SET Estado = 'Reservado' WHERE AlquilerID = @AlquilerID;
    COMMIT;
END;
GO
/****** Object:  StoredProcedure [dbo].[sp_CrearAlquiler]    Script Date: 19/10/2026 9:20:04 p. m. ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

/* =====================================================================
   4. PROCEDIMIENTOS
   ===================================================================== */

-- 4.1 Crear cotizacion (@Reservar = 0) o reserva directa (@Reservar = 1)
CREATE OR ALTER PROCEDURE [dbo].[sp_CrearAlquiler]
    @ClienteID       INT,
    @FechaInicio     DATE,
    @FechaFin        DATE,
    @Unidades        dbo.TipoListaUnidades READONLY,
    @PorcDescuento   DECIMAL(5,2)  = 0,
    @CostoTransporte DECIMAL(18,2) = 0,
    @Reservar        BIT           = 0,
    @AlquilerID      INT           OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;
    SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;  -- evita dobles reservas simultaneas

    IF @FechaFin < @FechaInicio THROW 50001, 'La fecha fin no puede ser anterior a la fecha de inicio.', 1;
    IF NOT EXISTS (SELECT 1 FROM @Unidades) THROW 50002, 'Debe indicar al menos una unidad.', 1;

    DECLARE @Dias INT = DATEDIFF(DAY, @FechaInicio, @FechaFin) + 1;
    DECLARE @Itbis DECIMAL(18,4) = (SELECT Valor FROM dbo.Parametro WHERE Clave = 'ITBIS');
    DECLARE @Sub DECIMAL(18,2), @Dep DECIMAL(18,2), @Desc DECIMAL(18,2), @Base DECIMAL(18,2), @ImpMonto DECIMAL(18,2);

    BEGIN TRAN;

    IF EXISTS (SELECT 1 FROM @Unidades l
               WHERE dbo.fn_UnidadDisponible(l.UnidadID, @FechaInicio, @FechaFin) = 0)
        THROW 50003, 'Una o mas unidades no estan disponibles en ese rango de fechas.', 1;

    INSERT dbo.Alquiler (ClienteID, FechaInicio, FechaFinPrevista, Estado, PorcDescuento, CostoTransporte)
    VALUES (@ClienteID, @FechaInicio, @FechaFin,
            CASE WHEN @Reservar = 1 THEN 'Reservado' ELSE 'Cotizado' END,
            @PorcDescuento, @CostoTransporte);
    SET @AlquilerID = SCOPE_IDENTITY();

    INSERT dbo.AlquilerDetalle (AlquilerID, UnidadID, Dias, Subtotal, Deposito)
    SELECT @AlquilerID, u.UnidadID, @Dias,
           dbo.fn_CalcularTarifa(u.EquipoID, @Dias), e.DepositoGarantia
    FROM @Unidades l
    JOIN dbo.Unidad u ON u.UnidadID = l.UnidadID
    JOIN dbo.Maquinaria e ON e.EquipoID = u.EquipoID;

    SELECT @Sub = SUM(Subtotal), @Dep = SUM(Deposito)
    FROM dbo.AlquilerDetalle WHERE AlquilerID = @AlquilerID;

    SET @Desc     = ROUND(@Sub * @PorcDescuento / 100, 2);
    SET @Base     = @Sub - @Desc + @CostoTransporte;
    SET @ImpMonto = ROUND(@Base * @Itbis, 2);

    UPDATE dbo.Alquiler
    SET Subtotal = @Sub, MontoDescuento = @Desc, ITBIS = @ImpMonto,
        Total = @Base + @ImpMonto, DepositoTotal = @Dep
    WHERE AlquilerID = @AlquilerID;

    COMMIT;
END;
GO
/****** Object:  StoredProcedure [dbo].[sp_DevolverAlquiler]    Script Date: 19/10/2026 9:20:04 p. m. ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

-- 4.5 Devolucion: calcula mora y danos, libera unidades o las manda a mantenimiento
CREATE OR ALTER PROCEDURE [dbo].[sp_DevolverAlquiler]
    @AlquilerID      INT,
    @FechaDevolucion DATE = NULL,
    @Danos           dbo.TipoListaDanos READONLY   -- solo las unidades con dano
AS
BEGIN
    SET NOCOUNT ON; SET XACT_ABORT ON;
    SET @FechaDevolucion = ISNULL(@FechaDevolucion, CAST(GETDATE() AS DATE));

    DECLARE @FinPrev DATE, @Mora DECIMAL(18,4), @Retraso INT,
            @PenMora DECIMAL(18,2), @PenDanos DECIMAL(18,2), @Pen DECIMAL(18,2),
            @DepPagado DECIMAL(18,2), @Retenido DECIMAL(18,2);

    SELECT @FinPrev = FechaFinPrevista FROM dbo.Alquiler WHERE AlquilerID = @AlquilerID AND Estado = 'Activo';
    IF @FinPrev IS NULL THROW 50010, 'El alquiler no existe o no esta activo.', 1;

    SET @Mora    = (SELECT Valor FROM dbo.Parametro WHERE Clave = 'RecargoMora');
    SET @Retraso = CASE WHEN @FechaDevolucion > @FinPrev THEN DATEDIFF(DAY, @FinPrev, @FechaDevolucion) ELSE 0 END;

    BEGIN TRAN;

    -- Mora = tarifa diaria de cada equipo x dias de retraso x (1 + recargo)
    SELECT @PenMora = ROUND(ISNULL(SUM(e.TarifaDiaria), 0) * @Retraso * (1 + @Mora), 2)
    FROM dbo.AlquilerDetalle d
    JOIN dbo.Unidad u ON u.UnidadID = d.UnidadID
    JOIN dbo.Maquinaria e ON e.EquipoID = u.EquipoID
    WHERE d.AlquilerID = @AlquilerID;

    SELECT @PenDanos = ISNULL(SUM(CostoDano), 0) FROM @Danos;
    SET @Pen = @PenMora + @PenDanos;

    UPDATE d SET EstadoDevolucion = 'Danada', CostoDano = x.CostoDano
    FROM dbo.AlquilerDetalle d JOIN @Danos x ON x.UnidadID = d.UnidadID
    WHERE d.AlquilerID = @AlquilerID;

    UPDATE dbo.AlquilerDetalle SET EstadoDevolucion = 'Devuelta'
    WHERE AlquilerID = @AlquilerID AND EstadoDevolucion = 'Pendiente';

    -- Unidades danadas: abrir registro de mantenimiento correctivo
    INSERT dbo.Mantenimiento (UnidadID, FechaInicio, Tipo, Descripcion)
    SELECT d.UnidadID, @FechaDevolucion, 'Correctivo',
           'Dano reportado en devolucion del alquiler ' + CAST(@AlquilerID AS VARCHAR(10))
    FROM dbo.AlquilerDetalle d
    WHERE d.AlquilerID = @AlquilerID AND d.EstadoDevolucion = 'Danada';

    -- Estado de cada unidad
    UPDATE u SET Estado = CASE WHEN d.EstadoDevolucion = 'Danada' THEN 'Mantenimiento' ELSE 'Disponible' END
    FROM dbo.Unidad u JOIN dbo.AlquilerDetalle d ON d.UnidadID = u.UnidadID
    WHERE d.AlquilerID = @AlquilerID;

    -- La penalidad se cubre primero con el deposito de garantia
    SELECT @DepPagado = ISNULL(SUM(Monto), 0) FROM dbo.Pago WHERE AlquilerID = @AlquilerID AND Tipo = 'Deposito';
    SET @Retenido = CASE WHEN @Pen < @DepPagado THEN @Pen ELSE @DepPagado END;

    UPDATE dbo.Alquiler
    SET Estado = 'Finalizado', FechaDevolucionReal = @FechaDevolucion,
        Penalidad = @Pen, DepositoRetenido = @Retenido
    WHERE AlquilerID = @AlquilerID;

    COMMIT;
END;
GO
/****** Object:  StoredProcedure [dbo].[sp_EntregarAlquiler]    Script Date: 19/10/2026 9:20:04 p. m. ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

-- 4.4 Entregar equipos al cliente (exige deposito completo)
CREATE OR ALTER PROCEDURE [dbo].[sp_EntregarAlquiler] @AlquilerID INT
AS
BEGIN
    SET NOCOUNT ON; SET XACT_ABORT ON;

    DECLARE @DepReq DECIMAL(18,2), @DepPag DECIMAL(18,2);
    SELECT @DepReq = DepositoTotal FROM dbo.Alquiler WHERE AlquilerID = @AlquilerID AND Estado = 'Reservado';
    IF @DepReq IS NULL THROW 50007, 'El alquiler no existe o no esta en estado Reservado.', 1;

    SELECT @DepPag = ISNULL(SUM(Monto), 0) FROM dbo.Pago WHERE AlquilerID = @AlquilerID AND Tipo = 'Deposito';
    IF @DepPag < @DepReq THROW 50008, 'El deposito de garantia no esta completo.', 1;

    BEGIN TRAN;
    UPDATE dbo.Alquiler SET Estado = 'Activo' WHERE AlquilerID = @AlquilerID;
    UPDATE u SET Estado = 'Alquilado'
    FROM dbo.Unidad u JOIN dbo.AlquilerDetalle d ON d.UnidadID = u.UnidadID
    WHERE d.AlquilerID = @AlquilerID;
    COMMIT;
END;
GO
/****** Object:  StoredProcedure [dbo].[sp_FinalizarMantenimiento]    Script Date: 19/10/2026 9:20:04 p. m. ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

CREATE OR ALTER PROCEDURE [dbo].[sp_FinalizarMantenimiento] @MantenimientoID INT, @Costo DECIMAL(18,2)
AS
BEGIN
    SET NOCOUNT ON; SET XACT_ABORT ON;
    DECLARE @UnidadID INT;
    SELECT @UnidadID = UnidadID FROM dbo.Mantenimiento WHERE MantenimientoID = @MantenimientoID AND FechaFin IS NULL;
    IF @UnidadID IS NULL THROW 50013, 'El mantenimiento no existe o ya fue cerrado.', 1;
    BEGIN TRAN;
    UPDATE dbo.Mantenimiento SET FechaFin = CAST(GETDATE() AS DATE), Costo = @Costo WHERE MantenimientoID = @MantenimientoID;
    UPDATE dbo.Unidad SET Estado = 'Disponible' WHERE UnidadID = @UnidadID;
    COMMIT;
END;
GO
/****** Object:  StoredProcedure [dbo].[sp_IniciarMantenimiento]    Script Date: 19/10/2026 9:20:04 p. m. ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

-- 4.7 Mantenimiento
CREATE OR ALTER PROCEDURE [dbo].[sp_IniciarMantenimiento]
    @UnidadID INT, @Tipo VARCHAR(12), @Descripcion VARCHAR(300) = NULL
AS
BEGIN
    SET NOCOUNT ON; SET XACT_ABORT ON;
    IF NOT EXISTS (SELECT 1 FROM dbo.Unidad WHERE UnidadID = @UnidadID AND Estado = 'Disponible')
        THROW 50012, 'Solo una unidad Disponible puede entrar a mantenimiento.', 1;
    BEGIN TRAN;
    INSERT dbo.Mantenimiento (UnidadID, FechaInicio, Tipo, Descripcion)
    VALUES (@UnidadID, CAST(GETDATE() AS DATE), @Tipo, @Descripcion);
    UPDATE dbo.Unidad SET Estado = 'Mantenimiento' WHERE UnidadID = @UnidadID;
    COMMIT;
END;
GO
/****** Object:  StoredProcedure [dbo].[sp_RegistrarPago]    Script Date: 19/10/2026 9:20:04 p. m. ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

-- 4.3 Registrar pagos (deposito, anticipo, pago o reembolso de deposito)
CREATE OR ALTER PROCEDURE [dbo].[sp_RegistrarPago]
    @AlquilerID INT, @Tipo VARCHAR(20), @Metodo VARCHAR(15),
    @Monto DECIMAL(18,2), @Referencia VARCHAR(60) = NULL
AS
BEGIN
    SET NOCOUNT ON; SET XACT_ABORT ON;

    IF NOT EXISTS (SELECT 1 FROM dbo.Alquiler WHERE AlquilerID = @AlquilerID AND Estado <> 'Cancelado')
        THROW 50005, 'El alquiler no existe o esta cancelado.', 1;

    IF @Tipo = 'ReembolsoDeposito'
    BEGIN
        DECLARE @PorReembolsar DECIMAL(18,2) =
            (SELECT DepositoPorReembolsar FROM dbo.vw_EstadoCuentaAlquiler WHERE AlquilerID = @AlquilerID);
        IF @Monto > @PorReembolsar
            THROW 50006, 'El reembolso supera el deposito disponible para devolver.', 1;
    END

    INSERT dbo.Pago (AlquilerID, Tipo, Metodo, Monto, Referencia)
    VALUES (@AlquilerID, @Tipo, @Metodo, @Monto, @Referencia);
END;
GO
