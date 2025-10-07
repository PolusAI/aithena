docker run -it -v /polus2/velezramirezc2/openalex-snapshot/data:/mnt/outdir --env FROM_DATE="20224-09-29" --env OUT_DIR="/mnt/outdir" polusai/get-openalex:0.1.0
docker run -it -v /polus2/velezramirezc2/openalex-snapshot/data:/mnt/outdir --env ALL_LAST_MONTH=1 --env OUT_DIR="/mnt/outdir" polusai/get-openalex:0.1.0
docker run --name nginx-ais -v /polus2/velezramirezc2/nginx/nginx.conf:/etc/nginx/nginx.conf:ro -p 80:80 --network=ais1 nginx
