## wrapper to generate cognitive association figures for manuscript

# arguments
args <- commandArgs(trailingOnly = TRUE)
if (is.na(args[1])) {
  fig_path <- file.path(
    "..", "..", "output", "analysis",
    "cognitive_association_figures"
  )
} else {
  fig_path <- args[1]
}
if (is.na(args[2]) || (args[2] == "TRUE")) {
  setwd(dirname(sys.frame(1)$ofile)) # set working directory
}
dir.create(fig_path, recursive = TRUE, showWarnings = FALSE)

# variables
exts <- c("_pretrained", "_finetuned")
settings <- list(
  list(
    name = "EDIS", pre = "bl_", yvar = "zExecutiveFunction",
    subset = "all", xlim = c(-30, 30), ylim = c(-6, 6),
    bold_p = TRUE
  ),
  list(
    name = "SLABS", pre = "bl_", yvar = "ch_ef",
    subset = "longitudinal", xlim = c(-25, 25),
    ylim = c(-3, 3), bold_p = FALSE
  ),
  list(
    name = "SLABS", pre = "ch_", yvar = "ch_ef",
    subset = "longitudinal", xlim = c(-5, 5), ylim = c(-3, 3),
    bold_p = TRUE
  ),
  list(
    name = "SLABS", pre = "ch_", yvar = "future_ch_ef",
    subset = "longitudinal", xlim = c(-5, 5), ylim = c(-5, 5),
    bold_p = TRUE
  ),
  list(
    name = "GUSTO", pre = "bl_", yvar = "kbit_iq",
    subset = "baseline", xlim = c(-2, 2), ylim = c(-60, 60),
    bold_p = FALSE
  ),
  list(
    name = "GUSTO", pre = "bl_", yvar = "nepsy_inhibition",
    subset = "longitudinal", xlim = c(-2.25, 2.25),
    ylim = c(-15, 15), bold_p = FALSE
  ),
  list(
    name = "GUSTO", pre = "ch_", yvar = "nepsy_inhibition",
    subset = "longitudinal", xlim = c(-2.25, 2.25),
    ylim = c(-15, 15), bold_p = TRUE
  )
)

# loop through settings
for (ext in exts) {
  for (setting in settings) {
    setting$ext <- ext
    if (setting$name == "GUSTO" && ext == "_pretrained") {
      setting$bold_p <- FALSE
    }

    # render markdown
    out_file <- file.path(fig_path, paste0(
      setting$name, "_", setting$pre, "BAG",
      setting$ext, "_", setting$yvar
    ))
    rmarkdown::render("plot_cognitive_results.Rmd",
      output_file = out_file, params = setting
    )
  }
}
