# arguments
while getopts "a:t:i:o:p:f:" var
do
   case "$var" in
       a) ANTS_PATH=${OPTARG};;
       t) TEMPLATE=${OPTARG};;
       i) INPUT_IMG=${OPTARG};;
       o) OUT_PATH=${OPTARG};;
       p) PRETRAINED_MAP=${OPTARG};;
       f) FINETUNED_MAP=${OPTARG};;
   esac
done

# setup
ID=$(basename ${INPUT_IMG} .nii.gz)
INTERM="${OUT_PATH}/intermediate/${ID}_"
mkdir -p $(dirname ${INTERM})

PRETRAINED_OUT="${OUT_PATH}/pretrained/${ID}.nii.gz"
mkdir -p $(dirname ${PRETRAINED_OUT})
FINETUNED_OUT="${OUT_PATH}/finetuned/${ID}.nii.gz"
mkdir -p $(dirname ${FINETUNED_OUT})

# calculate registration
sh ${ANTS_PATH}/antsRegistrationSyN.sh -d 3 -f ${TEMPLATE} \
    -m ${INPUT_IMG} -o ${INTERM}

# apply to pretrained map
antsApplyTransforms -d 3 -i ${PRETRAINED_MAP} -o ${PRETRAINED_OUT} \
    -r ${TEMPLATE} -t ${INTERM}1Warp.nii.gz -t ${INTERM}0GenericAffine.mat

# apply to finetuned map
antsApplyTransforms -d 3 -i ${FINETUNED_MAP} -o ${FINETUNED_OUT} \
    -r ${TEMPLATE} -t ${INTERM}1Warp.nii.gz -t ${INTERM}0GenericAffine.mat