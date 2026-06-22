package com.filimon_stefan.deskbudhydra.network;

import android.util.Log;

import androidx.annotation.NonNull;

import java.io.IOException;
import java.util.concurrent.TimeUnit;

import okhttp3.Call;
import okhttp3.Callback;
import okhttp3.MediaType;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;

public class ApiClient {
    private static final String TAG = "ApiClient";
    public static final MediaType JSON_MEDIA_TYPE = MediaType.parse("application/json; charset=utf-8");

    private static OkHttpClient client;

//    Facem Singleton pentru a nu avea mai multe instante de OkHttpClient
    public static OkHttpClient getCLient(){
        if (client == null){
            client = new OkHttpClient.Builder()
                    .connectTimeout(5, TimeUnit.SECONDS)
                    .readTimeout(5, TimeUnit.SECONDS)
                    .writeTimeout(5, TimeUnit.SECONDS)
                    .build();
        }
        return client;
    }

    public interface ApiCallback{
        void onSuccess(String response);
        void onFail(String eroare);
    }

    /**
     * Trimite un POST cu JSON la URL-ul specificat.
     * Răspunsul vine asincron pe ApiCallback (NU pe thread-ul UI!).
     */

    public static void post(String url, String jsonBody, ApiCallback callback){
        RequestBody body = RequestBody.create(JSON_MEDIA_TYPE, jsonBody);
        Request request = new Request.Builder()
                .url(url)
                .post(body)
                .build();

        getCLient().newCall(request).enqueue(new Callback() {
            @Override
            public void onFailure(@NonNull Call call, @NonNull IOException e) {
                Log.e(TAG, "Eroare la trimitere POST:" + url + " " + e.getMessage());
                callback.onFail(e.getMessage());
            }

            @Override
            public void onResponse(@NonNull Call call, @NonNull Response response) throws IOException {
                try (Response resp = response) {
                    String responseBody = resp.body() != null ? resp.body().string() : "";

                    if (resp.isSuccessful()){
                        Log.d(TAG, "POST trimis cu succes: " + url);
                        callback.onSuccess(responseBody);
                    }else {
                        Log.e(TAG, "POST esuat HTTP " + resp.code() + " " + responseBody);
                        callback.onFail("HTTP " + resp.code() + ": " + responseBody);
                    }
                }
            }
        });
    }

    /**
     * Trimite un GET la URL-ul specificat.
     */
    public static void get(String url, ApiCallback callback){
        Request request = new Request.Builder()
                .url(url)
                .get()
                .build();

        getCLient().newCall(request).enqueue(new Callback() {
            @Override
            public void onFailure(@NonNull Call call, @NonNull IOException e) {
                Log.e("TAG", "GET esuat: " + url + "  " + e.getMessage());
                callback.onFail(e.getMessage());
            }

            @Override
            public void onResponse(@NonNull Call call, @NonNull Response response) throws IOException {
                try (Response resp = response) {
                    String responseBody = resp.body() != null ? resp.body().string() : "";

                    if (resp.isSuccessful()){
                        Log.d(TAG, "GET a avut succes: " + url);
                        callback.onSuccess(responseBody);
                    }else {
                        Log.e(TAG, "GET esuat HTTP " + resp.code() + " " + responseBody);
                        callback.onFail("HTTP " + resp.code() + ": " + responseBody);
                    }
                }
            }
        });
    }
}
