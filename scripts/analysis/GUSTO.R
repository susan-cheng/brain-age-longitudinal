# define the GUSTO class

setClass("GUSTO",
  contains = "Study"
)

setMethod(
  "initialize",
  signature(.Object = "GUSTO"),
  function(.Object, name,
           path = file.path("..", "..", "data", "analysis", "GUSTO.csv"),
           exclude_path = file.path(
             "..", "..", "data", "analysis",
             "GUSTO_exclude.csv"
           ),
           base_colors = c(
             "royalblue1", "royalblue2", "royalblue3",
             "royalblue4"
           ),
           main_color = scales::alpha("royalblue", 0.75),
           color_by = "age_category",
           xlim = c(0, 17),
           ylim = c(0, 25),
           legend = c("4.5YO", "6.0YO", "7.5YO", "10.5YO"),
           domains = c(
             "wcst_tess", "nepsy_naming", "nepsy_inhibition",
             "nepsy_switching"
           ),
           covars = c("chron_age", "sex"),
           subset = "longitudinal") {
    # load
    .Object@name <- name
    .Object@is_longitudinal <- TRUE
    .Object@path <- path
    .Object@data_orig <- read.csv(.Object@path)
    .Object@domains <- domains
    .Object@covars <- covars
    .Object@subset <- subset
    if (subset == "baseline") {
      .Object@yvars <- "kbit_iq"
    } else {
      if (!subset == "longitudinal") {
        warning("Unknown subset given, longitudinal subset will be used.")
      }
      .Object@yvars <- domains
    }

    # exclusions
    .Object@data <- subset(
      .Object@data_orig,
      !stringr::str_detect(.Object@data_orig$SubID, "-")
    )
    .Object@data$SubID <- as.numeric(.Object@data$SubID)
    .Object@exclude_path <- exclude_path
    exclude <- read.csv(.Object@exclude_path)
    .Object@data <- dplyr::anti_join(.Object@data, exclude,
      by = c("SubID", "age_category")
    )

    # set data
    .Object@data_T1 <- .Object@data
    .Object@data_T1 <- tidyr::drop_na(
      .Object@data_T1, SubID, chron_age,
      pred_age_pretrained, pred_age_finetuned
    )
    .Object@data_T1 <- get_times(.Object@data_T1)
    .Object@data_cog <- .Object@data

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
  signature(.Object = "GUSTO"),
  function(.Object, yvar, pre, ext) {
    # set cognitive age
    if (.Object@subset == "baseline") {
      cog_age <- 4.5
    } else {
      cog_age <- 8.5
    }

    # select relevant data
    data <- .Object@data
    cols <- names(data)
    prefix <- sub("_.*", "", yvar)
    scores <- cols[startsWith(cols, prefix)]
    BAG <- paste0("BAG", ext)
    data_T1 <- na.omit(data[, c("SubID", "age_category", .Object@covars, BAG)])
    data_cog <- tidyr::drop_na(data, SubID, age_category, all_of(scores))
    data_cog <- subset(data_cog, data_cog$age_category == cog_age)
    data_cog <- data_cog[!is.na(as.numeric(data_cog[[yvar]])), ]
    data_cog[[yvar]] <- as.numeric(data_cog[[yvar]])

    # keep usable scores
    usability <- paste0(prefix, "_usability")
    if (usability %in% cols) {
      data_cog <- subset(data_cog, data_cog[[usability]] == 1)
    }

    if (.Object@subset == "baseline") {
      # prepare for cross-sectional analysis
      df <- na.omit(data_cog[, c("SubID", "ethnicity",
                                 .Object@covars, BAG, yvar)])
      names(df)[names(df) == BAG] <- paste0(pre, BAG)
    } else {
      # prepare for longitudinal analysis
      data_T1 <- get_long_data(subset(data_T1, data_T1$age_category < cog_age))
      data_T1 <- get_times(data_T1)
      df_T1 <- prepare_long_data(data_T1, var = BAG, covars = .Object@covars)
      df_cog <- subset(data_cog, select = c("SubID", "ethnicity", yvar))
      df <- merge(df_T1, df_cog, by = "SubID")
    }

    # check only one row per subject
    N <- nrow(df)
    if (N != nrow(get_uniq_data(df))) {
      warning("Merged data does not have one subject per row")
      print(get_long_data(df))
    }

    # return
    .Object@df <- df
    return(.Object)
  }
)
