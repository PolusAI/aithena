{{/*
Expand the name of the chart.
*/}}
{{- define "ask-aithena-agent-chart.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "ask-aithena-agent-chart.fullname" -}}
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
{{- define "ask-aithena-agent-chart.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "ask-aithena-agent-chart.labels" -}}
helm.sh/chart: {{ include "ask-aithena-agent-chart.chart" . }}
{{ include "ask-aithena-agent-chart.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- with .Values.commonLabels }}
{{ toYaml . }}
{{- end }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "ask-aithena-agent-chart.selectorLabels" -}}
app.kubernetes.io/name: {{ include "ask-aithena-agent-chart.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "ask-aithena-agent-chart.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "ask-aithena-agent-chart.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Get the secret name
*/}}
{{- define "ask-aithena-agent-chart.secretName" -}}
{{- if .Values.secret.existingSecret }}
{{- .Values.secret.existingSecret }}
{{- else }}
{{- include "ask-aithena-agent-chart.fullname" . }}-secret
{{- end }}
{{- end }}

{{/*
Get the PVC name
*/}}
{{- define "ask-aithena-agent-chart.pvcName" -}}
{{- include "ask-aithena-agent-chart.fullname" . }}-pvc
{{- end }}

{{/*
Get the PV name
*/}}
{{- define "ask-aithena-agent-chart.pvName" -}}
{{- include "ask-aithena-agent-chart.fullname" . }}-pv
{{- end }}

{{/*
Get the service name
*/}}
{{- define "ask-aithena-agent-chart.serviceName" -}}
{{- include "ask-aithena-agent-chart.fullname" . }}-service
{{- end }}

{{/*
Return the appropriate apiVersion for HPA
*/}}
{{- define "ask-aithena-agent-chart.hpa.apiVersion" -}}
{{- if semverCompare ">=1.23-0" .Capabilities.KubeVersion.GitVersion -}}
autoscaling/v2
{{- else -}}
autoscaling/v2beta2
{{- end -}}
{{- end -}}

{{/*
Get namespace
*/}}
{{- define "ask-aithena-agent-chart.namespace" -}}
{{- if .Values.namespace }}
{{- .Values.namespace }}
{{- else }}
{{- .Release.Namespace }}
{{- end }}
{{- end }}
