{{- define "chart.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "chart.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- $name := default .Chart.Name .Values.nameOverride -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}

{{- define "chart.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version -}}
{{- end -}}


{{- define "pv.name" -}}
{{- printf "%s-%s" "pv" .Release.Name -}}
{{- end -}}

{{- define "pvc.name" -}}
{{- printf "%s-%s" "pvc" .Release.Name -}}
{{- end -}}

{{- define "storage.name" -}}
{{- printf "%s-%s" "storage" .Release.Name -}}
{{- end -}}

{{- define "service.name" -}}
{{- printf "%s-%s" "service" .Release.Name -}}
{{- end -}}