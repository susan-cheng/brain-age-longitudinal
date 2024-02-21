# calculate time passed
get_times <- function(data) {
  data_bl <- get_uniq_data(data)
  for (i in seq_len(nrow(data_bl))) {
    subj <- data_bl[i, "SubID"]
    bl_age <- data_bl[i, "chron_age"]

    is_subj <- (data$SubID == subj)
    data[is_subj, "time"] <- data[is_subj, "chron_age"] - bl_age
  }
  return(data)
}

# add covariates and SubID to analysis dataframe
add_covariates <- function(df, data_bl, covars) {
  # covariates
  for (covar in covars) {
    if (length(unique(data_bl[[covar]])) > 1) {
      df[[covar]] <- data_bl[[covar]]
    } else {
      warning(sprintf(
        "Covariate '%s' only takes 1 value, will not be included",
        covar
      ))
    }
  }

  # SubID
  df$SubID <- data_bl$SubID

  return(df)
}

# prepare longitudinal data for linear regressions
prepare_long_data <- function(data, var = "BAG",
                              covars = c("chron_age", "sex", "yr_edu")) {
  data_bl <- get_uniq_data(data)

  # main variable
  bl_var <- data_bl[[var]]
  ch_var <- get_slopes(data, paste0(var, " ~ time"))
  df <- data.frame(bl_var, ch_var)
  names(df) <- c(bl(var), ch(var))

  # covariates
  df <- add_covariates(df, data_bl, covars)

  return(df)
}

# return data with >1 time point
get_long_data <- function(data) {
  tps <- table(data$SubID)
  cs_subjs <- as.numeric(names(subset(tps, tps == 1)))
  data_long <- subset(data, !(as.numeric(data$SubID) %in% cs_subjs))
  return(data_long)
}

# return first (or last) time point of each subject
get_uniq_data <- function(data, last = FALSE) {
  data_uniq <- data[!duplicated(data[, "SubID"], fromLast = last), ]
  return(data_uniq)
}

# return data at last time point
get_last_data <- function(data) {
  return(get_uniq_data(data, last = TRUE))
}

# get colors for each data point
get_colors <- function(data, color_by, colors) {
  if (is.null(color_by)) {
    return(colors)
  }
  x <- data[[color_by]]
  return(colors[match(x, sort(unique(x)))])
}

# add legend to figure
add_legend <- function(legend, colors, cex = 1.1) {
  if (!is.null(legend)) {
    legend("bottomright", legend = legend, fill = colors, cex = cex)
  }
}

# compare brain age predictions, e.g. before and after finetuning
compare_predictions <- function(data_T1, ext1, ext2) {
  xname <- paste0("pred_age", ext1)
  yname <- paste0("pred_age", ext2)
  x <- data_T1[[xname]]
  y <- data_T1[[yname]]
  r <- round(cor(x, y, method = "pearson"), 4)
  plot(x, y,
    pch = 19, col = scales::alpha("royalblue", 0.75), cex.lab = 1.25,
    xlim = NULL, ylim = NULL, panel.first = grid(lty = "solid"),
    xlab = var2name(xname), ylab = var2name(yname)
  )
  mtext(bquote("r =" ~ .(r)), cex = 1.75)
  abline(0, 1)
}

# run linear regression model
run_model <- function(df, xvar, yvar, covars = c("chron_age", "sex", "yr_edu"),
                      xlim = NULL, ylim = NULL, xlab = NULL, ylab = NULL,
                      colors = scales::alpha("blue", 0.75), cex.lab = 1.4) {
  # run
  covars <- paste(covars, collapse = " + ")
  formula <- paste0(yvar, " ~ ", xvar, " + ", covars)
  model <- lm(as.formula(formula), data = df)
  print("=== Main model: ===")
  print(summary(model))
  print(regclass::VIF(model))

  # axis labels
  if (is.null(xlab)) {
    xlab <- var2name(xvar)
  }
  if (is.null(ylab)) {
    ylab <- var2name(yvar)
  }

  # plot
  par(mar = c(5.1, 4.1, 4.2, 2.1))
  car::avPlots(model, xvar,
    id = FALSE, xlim = xlim, ylim = ylim,
    xlab = xlab, ylab = ylab, col = colors, col.lines = "black",
    cex.lab = cex.lab, pch = 19
  )

  # calculate change in R2
  base_formula <- paste0(yvar, " ~ ", covars)
  base_model <- lm(as.formula(base_formula), data = df)
  print("=== Base model (without variable of interest): ===")
  print(summary(base_model))
  delta_R2 <- summary(model)$adj.r.squared - summary(base_model)$adj.r.squared

  # return estimates
  coef <- summary(model)$coefficients[xvar, "Estimate"]
  pval <- summary(model)$coefficients[xvar, "Pr(>|t|)"]
  R2 <- summary(model)$r.squared
  return(list("coef" = coef, "pval" = pval, "R2" = R2, "delta_R2" = delta_R2))
}

# return linear regression slopes for each subject
get_slopes <- function(data_long, formula) {
  models <- plyr::dlply(data_long, "SubID", function(df) {
    lm(as.formula(formula), data = df)
  })
  df_model <- plyr::ldply(models, coef)
  return(df_model$time)
}

# add prefix to string
add_prefix <- function(string, pre) {
  return(paste0(pre, string))
}

# convenience function to add baseline prefix to every string
bl <- function(strings) {
  return(sapply(strings, add_prefix, pre = "bl_"))
}

# convenience function to add change prefix to every string
ch <- function(strings) {
  return(sapply(strings, add_prefix, pre = "ch_"))
}

# format p value for latex tables
format_p <- function(pvals) {
  new_pvals <- c()
  for (p in pvals) {
    if (is.na(p)) {
      p <- NA
    } else {
      if (p < 0.0001) {
        p <- "$\\mathbf{<0.0001}$"
      } else {
        p <- sprintf("%.4f", p)
        if (p < 0.05) {
          p <- paste0("\\textbf{", p, "}")
        }
      }
    }
    new_pvals <- c(new_pvals, p)
  }
  return(new_pvals)
}

# add text to results figure
add_text <- function(name, data, out, bold_p = FALSE) {
  p <- toString(signif(out$pval, digits = 3))
  if (bold_p) {
    p_str <- bquote(bold(p ~ "=" ~ .(p)))
  } else {
    p_str <- bquote(p ~ "=" ~ .(p))
  }
  mtext(
    bquote(bold(.(name) * ":") ~ "N =" ~ .(nrow(data)) * "," ~ .(p_str) ~
             "(\u0394" * R[adj]^2 ~ "=" ~
             .(format(round(out$delta_R2, 4), nsmall = 4)) * ")"),
    cex = 1.5
  )
}

# print mean and sd of follow up time for data
follow_up_time <- function(data) {
  data_last <- get_last_data(data)
  print("Mean follow up time:")
  print(mean(data_last$time))
  print("Standard deviation:")
  print(sd(data_last$time))
}

# convert list of variable names to plain English names
var2name <- function(pred_list) {
  pred_names <- c()
  for (pred in pred_list) {
    name <- switch(pred,
      "bl_BAG_pretrained" = "Baseline BAG (pretrained)",
      "bl_BAG_finetuned" = "Baseline BAG (finetuned)",
      "ch_BAG_pretrained" = "Change in BAG (pretrained)",
      "ch_BAG_finetuned" = "Change in BAG (finetuned)",
      
      "zGlobalscore" = "Baseline Global Cognition",
      "zExecutiveFunction" = "Baseline Executive Function",
      "zLanguage" = "Baseline Language",
      "zVerbalMemory" = "Baseline Verbal Memory",
      "zVisualMemory" = "Baseline Visual Memory",
      "zVisuoconstruction" = "Baseline Visuoconstruction",
      "zVisuomotorSpeed" = "Baseline Visuomotor Speed",
      "zAttention" = "Baseline Attention",
      
      "bl_global_cog" = "Baseline Global Cognition",
      "bl_ef" = "Baseline Executive Function",
      "bl_vm" = "Baseline Verbal Memory",
      "bl_vsm" = "Baseline Visual Memory",
      "bl_attn" = "Baseline Attention",
      "bl_proc_speed" = "Baseline Processing Speed",
      
      "ch_global_cog" = "Change in Global Cognition",
      "ch_ef" = "Change in Executive Function",
      "ch_vm" = "Change in Verbal Memory",
      "ch_vsm" = "Change in Visual Memory",
      "ch_attn" = "Change in Attention",
      "ch_proc_speed" = "Change in Processing Speed",
      
      "kbit_iq" = "Baseline KBIT-2 IQ",
      "nepsy_naming" = "Future Naming (NEPSY-II)",
      "nepsy_inhibition" = "Future Inhibition (NEPSY-II)",
      "nepsy_switching" = "Future Switching (NEPSY-II)",
      "wcst_tess" = "Future WCST Standard Score",
      pred
    )
    pred_names <- c(pred_names, name)
  }
  return(pred_names)
}
