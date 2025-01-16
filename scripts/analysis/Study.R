## define a general study class and constructor

setClass(
  "Study",
  representation(
    name = "character",
    is_longitudinal = "logical",
    path = "character",
    data_orig = "data.frame",
    exclude_path = "character",
    mmse_thr = "numeric",
    data = "data.frame",
    data_T1 = "data.frame",
    data_cog = "data.frame",
    base_colors = "vector",
    main_color = "character",
    colors = "vector",
    color_by = "character",
    xlim = "vector",
    ylim = "vector",
    legend = "vector",
    domains = "vector",
    yvars = "vector",
    covars = "vector",
    subset = "character",
    df = "data.frame"
  )
)

Study <- function(name, ...) {
  if (name == "EDIS") {
    return(new("EDIS", name = name, ...))
  } else if (name == "SLABS") {
    return(new("SLABS", name = name, ...))
  } else if (name == "GUSTO") {
    return(new("GUSTO", name = name, ...))
  } else if (name == "ADNI") {
    return(new("ADNI", name = name, ...))
  } else {
    stop("Unknown study name.")
  }
}

# common plotting variables
setGeneric("set_plotting", function(.Object, ...) {
  standardGeneric("set_plotting")
})
setMethod(
  "set_plotting",
  signature(.Object = "Study"),
  function(.Object, base_colors, color_by, xlim, ylim, legend) {
    .Object@base_colors <- base_colors
    .Object@colors <- scales::alpha(.Object@base_colors, 0.75)
    .Object@color_by <- color_by
    .Object@xlim <- xlim
    .Object@ylim <- ylim
    .Object@legend <- legend
    return(.Object)
  }
)

# plot brain age predictions
setGeneric("plot_predictions", function(.Object, ext) {
  standardGeneric("plot_predictions")
})
setMethod(
  "plot_predictions",
  signature(.Object = "Study"),
  function(.Object, ext = "") {
    # variables
    data <- .Object@data_T1
    chron_age <- data$chron_age
    pred_age <- data[[paste0("pred_age", ext)]]
    colors <- get_colors(data, .Object@color_by, .Object@colors)
    n <- nrow(get_uniq_data(data))
    r <- round(cor(chron_age, pred_age, method = "pearson"), 4)
    MAE <- format(round(mean(abs(pred_age - chron_age)), 4), nsmall = 4)

    # plot
    par(mar = c(5.1, 4.5, 4.1, 2.1))
    plot(chron_age, pred_age,
      pch = 19, col = colors, cex.lab = 1.75,
      xlim = .Object@xlim, ylim = .Object@ylim,
      panel.first = grid(lty = "solid"), xlab = "Chronological Age (years)",
      ylab = "Predicted Brain Age (years)"
    )
    abline(a = 0, b = 1)
    add_legend(.Object@legend, .Object@colors, cex = 1.3)
    mtext(bquote(bold(.(.Object@name) * ":") ~ "N =" ~ .(n) * ", r =" ~ .(r) *
                   ", MAE =" ~ .(MAE)), cex = 1.75)
  }
)

# run association with yvar and store results
setGeneric("run_association", function(.Object, yvar, pre, ext, res, row) {
  standardGeneric("run_association")
})
setMethod(
  "run_association",
  signature(.Object = "Study"),
  function(.Object, yvar, pre, ext, res, row) {
    xvar <- paste0(pre, "BAG", ext)
    covars <- .Object@covars

    # add baseline BAG as a covariate if testing change in BAG
    if (pre == "ch_") {
      covars <- c(covars, paste0("bl_BAG", ext))
    }

    # run
    out <- run_model(.Object@df, xvar, yvar, covars = covars)

    # store
    res$xvar[row] <- var2name(xvar)
    res$yvar[row] <- var2name(yvar)
    res$coef[row] <- out$coef
    res$CI_l[row] <- out$CI_l
    res$CI_u[row] <- out$CI_u
    res$p[row] <- out$pval
    res$delta_R2[row] <- out$delta_R2
    res$R2[row] <- out$R2
    return(res)
  }
)
