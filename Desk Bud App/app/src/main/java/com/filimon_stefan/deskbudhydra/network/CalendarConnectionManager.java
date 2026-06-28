package com.filimon_stefan.deskbudhydra.network;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;

import org.json.JSONObject;

import java.io.IOException;

import okhttp3.Call;
import okhttp3.Callback;
import okhttp3.FormBody;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;

public class CalendarConnectionManager {

    public static class Status {
        public final boolean configured;
        public final boolean connected;
        public Status(boolean configured, boolean connected) {
            this.configured = configured;
            this.connected = connected;
        }
    }

    public interface Listener<T> {
        void pe_succes(T rezultat);
        void pe_eroare(@Nullable String mesaj);
    }

    private final OkHttpClient client;
    private final String baseUrl;

    public CalendarConnectionManager(OkHttpClient client, String baseUrl) {
        this.client = client;
        this.baseUrl = baseUrl;
    }

    public void cere_status(Listener<Status> listener) {
        Request req = new Request.Builder()
                .url(baseUrl + "/calendar/status")
                .get()
                .build();
        client.newCall(req).enqueue(new Callback() {
            @Override public void onFailure(@NonNull Call call, @NonNull IOException e) {
                listener.pe_eroare(e.getMessage());
            }
            @Override public void onResponse(@NonNull Call call, @NonNull Response raspuns) {
                try (Response r = raspuns) {
                    if (!r.isSuccessful() || r.body() == null) {
                        listener.pe_eroare("status " + r.code());
                        return;
                    }
                    JSONObject j = new JSONObject(r.body().string());
                    listener.pe_succes(new Status(
                            j.optBoolean("configured", false),
                            j.optBoolean("connected", false)
                    ));
                } catch (Exception e) {
                    listener.pe_eroare(e.getMessage());
                }
            }
        });
    }

    public void porneste_conectare(Listener<String> listener) {
        Request req = new Request.Builder()
                .url(baseUrl + "/calendar/start")
                .post(RequestBody.create(new byte[0], null))
                .build();
        client.newCall(req).enqueue(new Callback() {
            @Override public void onFailure(@NonNull Call call, @NonNull IOException e) {
                listener.pe_eroare(e.getMessage());
            }
            @Override public void onResponse(@NonNull Call call, @NonNull Response raspuns) {
                try (Response r = raspuns) {
                    if (!r.isSuccessful() || r.body() == null) {
                        listener.pe_eroare("start " + r.code());
                        return;
                    }
                    JSONObject j = new JSONObject(r.body().string());
                    String url = j.optString("auth_url", "");
                    if (url.isEmpty()) listener.pe_eroare("no auth_url");
                    else listener.pe_succes(url);
                } catch (Exception e) {
                    listener.pe_eroare(e.getMessage());
                }
            }
        });
    }

    public void trimite_cod(String cod, Listener<Boolean> listener) {
        FormBody body = new FormBody.Builder().add("cod", cod).build();
        Request req = new Request.Builder()
                .url(baseUrl + "/calendar/connect")
                .post(body)
                .build();
        client.newCall(req).enqueue(new Callback() {
            @Override public void onFailure(@NonNull Call call, @NonNull IOException e) {
                listener.pe_eroare(e.getMessage());
            }
            @Override public void onResponse(@NonNull Call call, @NonNull Response raspuns) {
                try (Response r = raspuns) {
                    listener.pe_succes(r.isSuccessful());
                }
            }
        });
    }

    public void deconecteaza(Listener<Boolean> listener) {
        Request req = new Request.Builder()
                .url(baseUrl + "/calendar/disconnect")
                .post(RequestBody.create(new byte[0], null))
                .build();
        client.newCall(req).enqueue(new Callback() {
            @Override public void onFailure(@NonNull Call call, @NonNull IOException e) {
                listener.pe_eroare(e.getMessage());
            }
            @Override public void onResponse(@NonNull Call call, @NonNull Response raspuns) {
                try (Response r = raspuns) {
                    listener.pe_succes(r.isSuccessful());
                }
            }
        });
    }
}