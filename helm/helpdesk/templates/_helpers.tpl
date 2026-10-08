{{- define "helpdesk.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 40 | trimSuffix "-" -}}
{{- end -}}

{{- define "helpdesk.fullname" -}}
{{- printf "%s-%s" .Release.Name (include "helpdesk.name" .) | trunc 40 | trimSuffix "-" -}}
{{- end -}}

{{- define "helpdesk.labels" -}}
app.kubernetes.io/name: {{ include "helpdesk.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
{{- end -}}

{{- define "helpdesk.selector" -}}
app.kubernetes.io/name: {{ include "helpdesk.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{- define "helpdesk.dbSecretName" -}}
{{- default (printf "%s-db" (include "helpdesk.fullname" .)) .Values.postgres.existingSecret -}}
{{- end -}}

{{- define "helpdesk.image" -}}
{{- printf "%s:%s" .image.repository (default $.Chart.AppVersion .image.tag) -}}
{{- end -}}
