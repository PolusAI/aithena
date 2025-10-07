{{/*
Expand the name of the chart.
*/}}
{{- define "litellm-db-chart.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "litellm-db-chart.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "litellm-db-chart.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "litellm-db-chart.labels" -}}
helm.sh/chart: {{ include "litellm-db-chart.chart" . }}
{{ include "litellm-db-chart.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "litellm-db-chart.selectorLabels" -}}
app.kubernetes.io/name: {{ include "litellm-db-chart.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the secret to use
*/}}
{{- define "litellm-db-chart.secretName" -}}
{{- if .Values.auth.existingSecret }}
{{- .Values.auth.existingSecret }}
{{- else }}
{{- include "litellm-db-chart.fullname" . }}-secret
{{- end }}
{{- end }}

{{/*
Create the name of the PVC to use
*/}}
{{- define "litellm-db-chart.pvcName" -}}
{{- include "litellm-db-chart.fullname" . }}-pvc
{{- end }}

{{/*
Create the name of the PV to use
*/}}
{{- define "litellm-db-chart.pvName" -}}
{{- if .Values.persistence.volumeName }}
{{- .Values.persistence.volumeName }}
{{- else }}
{{- include "litellm-db-chart.fullname" . }}-pv
{{- end }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "litellm-db-chart.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "litellm-db-chart.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}
