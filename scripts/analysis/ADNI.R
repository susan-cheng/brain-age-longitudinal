## (preliminary) define the ADNI class

setClass("ADNI",
         contains = "Study"
)

setMethod(
  "initialize",
  signature(.Object = "ADNI"),
  function(.Object, name,
           path = file.path("..", "..", "data", "analysis", "ADNI.csv"),
           exclude_path = file.path(
             "..", "..", "data", "analysis",
             "ADNI_exclude.csv"
           ),
           base_colors = c("navajowhite4", "navajowhite2"),
           color_by = "DX",
           xlim = c(50, 100),
           ylim = c(30, 100),
           legend = c("CN", "MCI"),
           domains = c("PHC_MEM", "PHC_EXF", "PHC_LAN", "PHC_VSP"),
           covars = c("chron_age", "sex", "yr_edu"),
           subset = "future") {
    # load
    .Object@name <- name
    .Object@is_longitudinal <- TRUE
    .Object@path <- path
    .Object@data_orig <- read.csv(.Object@path)
    .Object@domains <- domains
    .Object@covars <- covars
    .Object@subset <- subset
    if (subset == "baseline") {
      .Object@yvars <- bl(domains)
    } else if (subset == "future") {
      .Object@yvars <- sapply(.Object@domains, add_prefix, pre = "future_")
    } else {
      warning("Unknown subset given, future subset will be used.")
      .Object@yvars <- sapply(.Object@domains, add_prefix, pre = "future_")
    }
    
    # exclusions
    .Object@exclude_path <- exclude_path
    exclude <- read.csv(.Object@exclude_path)
    .Object@data <- dplyr::anti_join(.Object@data_orig, exclude,
                                     by = c("SubID", "ImgID")
    )
    
    # set data
    .Object@data_T1 <- tidyr::drop_na(
      .Object@data, SubID, chron_age, pred_age_pretrained
    )
    .Object@data_T1 <- get_times(.Object@data_T1)
    .Object@data_cog <- tidyr::drop_na(
      .Object@data, SubID, all_of(covars)
    )
    
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
  signature(.Object = "ADNI"),
  function(.Object, yvar, pre, ext) {
    BAG <- paste0("BAG", ext)
    if (.Object@subset == "baseline") {
      # prepare yvar
      if (startsWith(yvar, "bl_")) {
        domain <- sub("bl_", "", yvar)
      } else {
        stop(sprintf("Dependent variable '%s' not supported", yvar))
      }
      
      # baseline data
      data <- tidyr::drop_na(.Object@data, SubID, all_of(.Object@covars),
                             all_of(BAG), all_of(domain))
      data_bl <- get_uniq_data(data)
      .Object@data_T1 <- data_bl
      .Object@data_cog <- data_bl
      
      # prepare dataframe
      xvar <- data_bl[[BAG]]
      df <- data.frame(xvar)
      names(df) <- c(bl(BAG))
      df <- add_covariates(df, data_bl, .Object@covars)
      df[[yvar]] <- data_bl[[domain]]
      
    } else if (.Object@subset == "future") {
      # prepare yvar
      if (startsWith(yvar, "future_")) {
        domain <- sub("future_", "", yvar)
      } else {
        stop(sprintf("Dependent variable '%s' not supported", yvar))
      }
      
      # select data
      data_cog <- tidyr::drop_na(.Object@data, SubID, all_of(domain))
      data_last <- get_last_data(data_cog)
      data_T1 <- dplyr::anti_join(.Object@data, data_last, 
                                 by=c("SubID", "ImgID"))
      data_T1 <- tidyr::drop_na(data_T1, SubID, all_of(.Object@covars),
                               all_of(BAG))
      data_T1 <- get_long_data(data_T1)
      data_T1 <- get_times(data_T1)
      
      # prepare dataframe
      df <- prepare_long_data(data_T1, var = BAG, covars = .Object@covars)
      df <- merge(df, data_last[, c("SubID", domain)], by = "SubID")
      names(df)[names(df) == domain] <- yvar
    }  
    
    # return
    .Object@df <- df
    return(.Object)
  }
)

