package com.filimon_stefan.deskbudhydra.network;

import android.content.Context;
import android.util.Log;

import com.filimon_stefan.deskbudhydra.preparation.PrefsHelper;

import org.json.JSONException;
import org.json.JSONObject;

import java.time.LocalDate;

public class HydrationApiApp {
    private static final String TAG = "HydrationApi";
    private static final int PORT = 5000;

    private final String baseUrl;

    public HydrationApiApp(Context context) {
        PrefsHelper prefs = new PrefsHelper(context);
        String ip = prefs.getPiIp();
        this.baseUrl = "http://" + ip + ":" + PORT;
    }

    public void trimiteStatus(int mlBauti, int goal, ApiClient.ApiCallback callback){
        try {
            int procent = goal > 0 ? (int) Math.round((mlBauti * 100.0) / goal) : 0;
            String dataAzi = LocalDate.now().toString();

            JSONObject json = new JSONObject();
            json.put("ml_bauti", mlBauti);
            json.put("goal", goal);
            json.put("procent", procent);
            json.put("data", dataAzi);

            String url = baseUrl + "/api/hydration/status";
            Log.d(TAG, "Trimitem status la " + url + " " + json.toString());
            ApiClient.post(url, json.toString(), callback);
        } catch (JSONException e){
            Log.e(TAG, "Eroare la crearea JSON-ului pentru status: " + e.getMessage());
            callback.onFail("Eroare JSON :" + e.getMessage());
        }
    }

//    Test conexiune cu Pi
    public void ping(ApiClient.ApiCallback callback){
        String url = baseUrl + "/api/ping";
        Log.d(TAG, "Trimitem ping la " + url);
        ApiClient.get(url, callback);
    }
}
