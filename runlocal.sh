docker run -it  \
    -e "KONG_DATABASE=off" \
    -e "AWX_URL=ap-dev.npd.CHANGEME.com" \
    -e "AWX_TOKEN=KYCvAESYROBQ97eY6cAlvQLBYPJT9H" \
    -p 8000:8000 \
   CHANGEMEontainerreg.CHANGEME.com/sosa/automation-CHANGEMEpi-container:0.0.3

