from RPCANet_Code.dulrs_package.dulrs.dulrs_medical_defect_unfinish import dulrs_class_1

# Initial model
dulrs = dulrs_class_1(
    model_name="rpcanetma9", 
    model_path="/Users/yourname/My_mission/API/RPCANet_Code/result/20240519T07-24-39_rpcanetma9_nudt/best.pkl",     # Path for pretrained parameters
    use_cuda=True)

# For heatmap generation
heatmap = dulrs.heatmap(
    img_type = "medical",
    img_path="/Users/yourname/My_mission/Medical_RPCANet++/Medical_dataset/DRIVE/test/images/13.png",
    data_name="DRIVE_test_images_13",
    output_mat="./heatmap_test_3.10/mat",  # If users want to save the data as mat format. Default=None
    output_png="./heatmap_test_3.10/png"   # If users want to save the figure as png format. Default=None
)

## For lowrank calculation
#lowrank_matrix = dulrs.lowrank_cal(
#    img_path="/Users/yourname/My_mission/API/RPCANet_Code/datasets/test",
#    model_name="rpcanetma9",
#    data_name="test",
#    save_dir= './mats/lowrank' # Save path for result with mat format
#)
#
## For lowrank paint based on calculation
#lowrank_matrix_draw = dulrs.lowrank_draw(
#    model_name="rpcanetma9",
#    data_name="test",
#    mat_dir= './mats/lowrank',         
#    save_dir = './mats/lowrank/figure' # Save path for result with png format
#)
#
## For sparsity calculation
#sparsity_matrix = dulrs.sparsity_cal(
#    img_path="/Users/yourname/My_mission/API/RPCANet_Code/datasets/test",
#    model_name="rpcanetma9",
#    data_name="test",
#    save_dir = './mats/sparsity'        # Save path for result with mat format
#)