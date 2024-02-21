packages <- c("rmarkdown", "scales", "tidyr", "dplyr", "plyr", "xtable", 
              "stringr", "regclass", "car")
for (package in packages) {
  if (!require(package, quietly = TRUE)) {
    install.packages(package, dependencies = TRUE)
  }
}