## wrapper to generate cognitive association tables for manuscript

# arguments
args <- commandArgs(trailingOnly = TRUE)
if (is.na(args[1])) {
  table_path <- file.path(
    "..", "..", "output", "analysis",
    "cognitive_association_tables"
  )
} else {
  table_path <- args[1]
}
if (is.na(args[2]) || (args[2] == "TRUE")) {
  setwd(dirname(sys.frame(1)$ofile)) # set working directory
}

# variables
names <- c("EDIS", "SLABS", "GUSTO")
pres <- c("bl_", "ch_")
exts <- c("_pretrained", "_finetuned")

# paths
html_out_path <- file.path(table_path, "html")
csv_out_path <- file.path(table_path, "csv")
dir.create(html_out_path, recursive = TRUE, showWarnings = FALSE)
dir.create(csv_out_path, recursive = TRUE, showWarnings = FALSE)

# loop through settings
for (name in names) {
  if (name == "EDIS") {
    subsets <- c("all")
  } else {
    subsets <- c("baseline", "longitudinal")
  }
  for (subset in subsets) {
    for (pre in pres) {
      for (ext in exts) {
        setting <- list()
        setting$name <- name
        setting$pre <- pre
        setting$ext <- ext
        setting$subset <- subset
        setting$csv_out_path <- csv_out_path

        # render markdown
        out_file <- file.path(html_out_path, paste0(name, "_", pre, "BAG", ext))
        if (!is.na(subset)) {
          out_file <- paste0(out_file, "_", subset)
        }
        rmarkdown::render("run_cognitive_associations.Rmd",
          output_file = out_file, params = setting
        )
      }
      # baseline only
      if (name == "EDIS" || subset == "baseline") {
        break
      }
    }
  }
}
