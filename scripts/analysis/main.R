## generate analysis results seen in manuscript and store in output

# setup
setwd(dirname(sys.frame(1)$ofile))
out_path <- file.path("..", "..", "output", "analysis")
dir.create(out_path, recursive = TRUE, showWarnings = FALSE)

# plot brain age predictions
pred_path <- file.path(out_path, "brain_age_predictions")
dir.create(pred_path, recursive = TRUE, showWarnings = FALSE)
rmarkdown::render("plot_brain_age_predictions.Rmd", output_dir = pred_path)

# generate cognitive association tables
table_path <- file.path(out_path, "cognitive_association_tables")
system(paste("Rscript run_all_cognitive_associations.R", table_path, FALSE))

# plot cognitive association figures
fig_path <- file.path(out_path, "cognitive_association_figures")
system(paste("Rscript plot_all_cognitive_results.R", fig_path, FALSE))
