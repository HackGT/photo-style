git submodule sync
git submodule update --init --recursive
conda install pytorch=0.4.0
pip install flask
pip install flask_cors
pip install sendgrid
pip install google-cloud-storage
pip install python-dotenv
pip install pillow
pip install scikit-image
pip install opencv-python
pip install packaging
pip install pyyaml
pip install pycocotools
cd DetectronPytorch/lib/
. make.sh
cd ../
mkdir data/
cd data/
wget https://dl.fbaipublicfiles.com/detectron/36494496/12_2017_baselines/e2e_mask_rcnn_X-101-64x4d-FPN_1x.yaml.07_50_11.fkwVtEvg/output/train/coco_2014_train%3Acoco_2014_valminusminival/generalized_rcnn/model_final.pkl
mv model_final.pkl model_final.101.pkl
cd ../../
echo "Setup finished"
