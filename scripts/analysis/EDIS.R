## define the EDIS class

setClass("EDIS",
  contains = "Study"
)

setMethod(
  "initialize",
  signature(.Object = "EDIS"),
  function(.Object, name,
           path = file.path("..", "..", "data", "analysis", "EDIS.csv"),
           exclude_path = file.path(
             "..", "..", "data", "analysis",
             "EDIS_exclude.csv"
           ),
           mmse_thr = 10,
           base_colors = c("mediumorchid4", "mediumorchid1"),
           color_by = "dx",
           xlim = c(50, 100),
           ylim = c(30, 100),
           legend = c("NCI", "CIND"),
           domains = c(
             "zGlobalscore", "zExecutiveFunction", "zAttention",
             "zLanguage", "zVisuomotorSpeed", "zVisuoconstruction",
             "zVerbalMemory", "zVisualMemory"
           ),
           covars = c("chron_age", "sex", "yr_edu"),
           subset = "all") {
    # load
    .Object@name <- name
    .Object@is_longitudinal <- FALSE
    .Object@path <- path
    .Object@data_orig <- read.csv(.Object@path)
    .Object@mmse_thr <- mmse_thr
    .Object@domains <- domains
    .Object@yvars <- domains
    .Object@covars <- covars
    .Object@subset <- subset

    # exclusions
    .Object@exclude_path <- exclude_path
    exclude <- read.csv(.Object@exclude_path)
    .Object@data <- subset(.Object@data_orig, !(SubID %in% exclude$SubID))
    .Object@data <- subset(.Object@data, mmse >= mmse_thr)

    # keep and recode NCI and CIND
    .Object@data <- subset(.Object@data, dx < 3)
    .Object@data$dx <- as.numeric(.Object@data$dx > 0) + 1
    if (subset == "all") {
      .Object@data <- .Object@data
    } else if (subset == "NCI_only") {
      .Object@data <- subset(.Object@data, dx == 1)
    } else if (subset == "CIND_only") {
      .Object@data <- subset(.Object@data, dx == 2)
    } else {
      warning("Unknown subset given, all participants will be used.")
    }

    # set data
    .Object@data_T1 <- .Object@data
    .Object@data_cog <- .Object@data

    # plotting
    .Object <- set_plotting(.Object, base_colors, color_by, xlim, ylim, legend)
    return(.Object)
  }
)

# prepare data for analysis with yvar
setGeneric("prepare_for_analysis", function(.Object, yvar, pre, ext) {
  standardGeneric("prepare_for_analysis")
})
setMethod(
  "prepare_for_analysis",
  signature(.Object = "EDIS"),
  function(.Object, yvar, pre, ext) {
    # set dataframe
    covars <- .Object@covars
    .Object@df <- dplyr::select(
      .Object@data, SubID, dx, ethnicity,
      all_of(c(covars, yvar))
    )
    .Object@df[[paste0(pre, "BAG", ext)]] <- .Object@data[[paste0("BAG", ext)]]

    # info
    print("# of NCI:")
    print(sum(.Object@df$dx == 1))
    print("# of CIND:")
    print(sum(.Object@df$dx == 2))

    return(.Object)
  }
)
