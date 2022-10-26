#------------------------------------------------#
# Zip the Project files
# This terraform component will zip the terraform code 
# that will be executed during SageMaker Project Creation
#-----------------------#

data "external" "build_dir" {
  program = ["bash", "${path.module}/bin/dir_md5.sh", "${local.sm_project_folder}/"]
}

resource "null_resource" "remove_tf_code_zip" {
  triggers = {
    build_folder_content_md5 = data.external.build_dir.result.md5
  }
  provisioner "local-exec" {
    command = "/bin/rm -rf ${local.output_files}/${local.output_tf_zip_folder}.zip;"
  }
}

data "archive_file" "update_tf_code_zip" {
  depends_on  = [null_resource.remove_tf_code_zip]
  type        = "zip"
  output_path = "${local.output_files}/${local.output_tf_zip_folder}.zip"
  source_dir  = "${local.sm_project_folder}/"
}
