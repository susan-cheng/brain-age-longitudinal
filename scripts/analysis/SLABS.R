## define the SLABS class

setClass("SLABS",
  contains = "Study"
)

setMethod(
  "initialize",
  signature(.Object = "SLABS"),
  function(.Object, name,
           path = file.path("..", "..", "data", "analysis", "SLABS.csv"),
           mmse_thr = 26,
           base_colors = c("coral", "coral1", "coral2", "coral3", "coral4"),
           main_color = scales::alpha("coral3", 0.75),
           color_by = "phase",
           xlim = c(50, 100),
           ylim = c(30, 100),
           legend = c("Phase 1", "Phase 2", "Phase 3", "Phase 4", "Phase 5"),
           domains = c("global_cog", "ef", "vm", "vsm", "attn", "proc_speed"),
           covars = c("chron_age", "sex", "yr_edu"),
           subset = "longitudinal") {
    # load
    .Object@name <- name
    .Object@is_longitudinal <- TRUE
    .Object@path <- path
    .Object@data_orig <- read.csv(.Object@path)
    .Object@mmse_thr <- mmse_thr
    .Object@domains <- domains
    .Object@covars <- covars
    .Object@subset <- subset
    if (subset == "baseline") {
      .Object@yvars <- bl(domains)
    } else {
      if (!subset == "longitudinal") {
        warning("Unknown subset given, longitudinal subset will be used.")
      }
      .Object@yvars <- ch(domains)
    }

    # set data
    .Object@data <- tidyr::drop_na(.Object@data_orig, all_of(.Object@covars))
    .Object@data_T1 <- .Object@data
    .Object@data_cog <- .Object@data
    .Object <- filter_mmse(.Object)

    # plotting
    .Object <- set_plotting(.Object, base_colors, color_by, xlim, ylim, legend)
    .Object@main_color <- main_color
    return(.Object)
  }
)

# prepare data for analysis with yvar
setGeneric("prepare_for_analysis", function(.Object, yvar, pre, ext) {
  standardGeneric("prepare_for_analysis")
})
setMethod(
  "prepare_for_analysis",
  signature(.Object = "SLABS"),
  function(.Object, yvar, pre, ext) {
    # data availability
    BAG <- paste0("BAG", ext)
    .Object@data <- tidyr::drop_na(
      .Object@data, SubID, all_of(.Object@covars),
      all_of(BAG), all_of(.Object@domains)
    )
    if (.Object@subset == "baseline") {
      # baseline data
      data_bl <- get_uniq_data(.Object@data)
      .Object@data_T1 <- data_bl
      .Object@data_cog <- data_bl

      # prepare BAG and covariates
      xvar <- data_bl[[BAG]]
      df <- data.frame(xvar)
      names(df) <- c(bl(BAG))
      df <- add_covariates(df, data_bl, .Object@covars)

      # prepare yvar
      if (startsWith(yvar, "bl_")) {
        domain <- sub("bl_", "", yvar)
        df[[yvar]] <- data_bl[[domain]]
      } else {
        stop(sprintf("Dependent variable '%s' not supported", yvar))
      }
    } else {
      # longitudinal data
      .Object@data <- tidyr::drop_na(.Object@data, phase, time, mmse)
      .Object <- select_data(.Object)
      .Object <- filter_mmse(.Object)

      # prepare BAG and covariates
      df <- prepare_long_data(.Object@data_T1, var = BAG,
                              covars = .Object@covars)

      # prepare yvar
      if (startsWith(yvar, "future_")) {
        .Object <- remove_overlap(.Object)
        yvar <- sub("future_", "", yvar)
      }
      if (startsWith(yvar, "ch_")) {
        domain <- sub("ch_", "", yvar)
        ch_cog <- get_slopes(.Object@data_cog, paste0(domain, " ~ time"))
        df[[yvar]] <- ch_cog
      } else {
        stop(sprintf("Dependent variable '%s' not supported", yvar))
      }
    }

    # info
    print("T1 data:")
    follow_up_time(.Object@data_T1)
    print("Cognitive data:")
    follow_up_time(.Object@data_cog)

    # return
    .Object@df <- df
    return(.Object)
  }
)

# filter by MMSE at baseline
setGeneric("filter_mmse", function(.Object) {
  standardGeneric("filter_mmse")
})
setMethod(
  "filter_mmse",
  signature(.Object = "SLABS"),
  function(.Object) {
    NCI_bl <- subset(get_uniq_data(.Object@data_T1), mmse >= .Object@mmse_thr)
    .Object@data_T1 <- subset(.Object@data_T1, SubID %in% NCI_bl$SubID)
    .Object@data_cog <- subset(.Object@data_cog, SubID %in% NCI_bl$SubID)
    .Object@data <- subset(.Object@data, SubID %in% NCI_bl$SubID)
    return(.Object)
  }
)

# select participants with longitudinal T1 and cognitive data in the first
# three phases + additional cognitive data in the last two phases
setGeneric("select_data", function(.Object) {
  standardGeneric("select_data")
})
setMethod(
  "select_data",
  signature(.Object = "SLABS"),
  function(.Object) {
    # get longitudinal T1 and cognitive data
    data_T1 <- get_long_data(subset(.Object@data, phase <= 3))
    data_cog <- get_long_data(.Object@data)

    # match subjects
    data_cog <- subset(data_cog, SubID %in% data_T1$SubID)
    with_future_cog <- subset(get_last_data(data_cog), phase > 3)
    data_cog <- subset(data_cog, SubID %in% with_future_cog$SubID)
    data_T1 <- subset(data_cog, phase <= 3)

    # sort
    .Object@data_T1 <- data_T1[order(data_T1$SubID, data_T1$phase), ]
    .Object@data_cog <- data_cog[order(data_cog$SubID, data_cog$phase), ]

    return(.Object)
  }
)

# remove overlapping change intervals
setGeneric("remove_overlap", function(.Object) {
  standardGeneric("remove_overlap")
})
setMethod(
  "remove_overlap",
  signature(.Object = "SLABS"),
  function(.Object) {
    overlap <- dplyr::anti_join(.Object@data_T1, get_last_data(.Object@data_T1),
      by = c("SubID", "phase")
    )
    .Object@data_cog <- dplyr::anti_join(.Object@data_cog, overlap,
      by = c("SubID", "phase")
    )
    return(.Object)
  }
)
