package com.filimon_stefan.deskbudhydration.preparation;

import android.content.Context;
import android.content.SharedPreferences;

import com.google.gson.Gson;
import com.google.gson.reflect.TypeToken;
import java.lang.reflect.Type;
import java.util.ArrayList;
import java.util.List;

public class PrefsHelper {
    private static final String PREFS_NAME = "deskbud_hydration_prefs";

//    Cheile pentru fiecare valoare salvata
    private static final String KEY_GREUTATE = "greutate";
    private static final String KEY_GEN = "gen";
    private static final String KEY_GOAL = "goal_zilnic";
    private static final String KEY_ML_GOAL = "ml_baut_azi";
    private static final String KEY_DATA_ZI_PRECEDENTA = "data_zi_precedenta";
    private static final String KEY_ISTORIC = "istoric_zile";

    private final SharedPreferences prefs;
    private final Gson gson;

    public PrefsHelper(Context context){
        prefs = context.getApplicationContext()
                .getSharedPreferences(PREFS_NAME,Context.MODE_PRIVATE);
        gson = new Gson();
    }

//    GREUTATE
    public float getGreutate(){
        return prefs.getFloat(KEY_GREUTATE,0f);
    }

    public void setGreutate(float greutate){
        prefs.edit().putFloat(KEY_GREUTATE, greutate).apply();
    }

//    gen
    public String getGen(){
        return prefs.getString(KEY_GEN, "");
    }

    public void setGen(String gen){
        prefs.edit().putString(KEY_GEN, gen).apply();
    }

//    GOAL ZILNIC (ml)
    public int getGoal(){
        return prefs.getInt(KEY_GOAL, 2000); // setam default 2L apa
    }

    public void setGoal(int goal){
        prefs.edit().putInt(KEY_GOAL, goal).apply();
    }

    public boolean aFolositCalculator(){
        return getGreutate() > 0 && !getGen().isEmpty();
    }

//    ML BAUTI AZI
    public int getMlBautiAzi(){
        return prefs.getInt(KEY_ML_GOAL, 0);
    }

    public void setMlBautiAzi(int ml){
        if (ml < 0){
            prefs.edit().putInt(KEY_ML_GOAL, 0).apply();
        }else{
            prefs.edit().putInt(KEY_ML_GOAL, ml).apply();
        }
    }

    public void adaugaMlBauti(int ml){
        setMlBautiAzi(getMlBautiAzi() + ml);
    }

    public void scadeMlBauti(int ml){
        setMlBautiAzi(getMlBautiAzi() - ml);
    }

    public void reseteazaMlBautiAzi(){
        setMlBautiAzi(0);
    }

//    DATA ZI PRECEDENTA (folosita pentru reset)
    public String getZiPrecedenta(){
        return prefs.getString(KEY_DATA_ZI_PRECEDENTA, "");
    }

    public void setZiPrecedenta(String data){
        prefs.edit().putString(KEY_DATA_ZI_PRECEDENTA, data).apply();
    }

//    ISTORIC ZILE
    public List<ZiIstoric> getIstoric(){
        String json = prefs.getString(KEY_ISTORIC, "");
        if(json.isEmpty()){
            return new ArrayList<>();
        }
        Type type = new TypeToken<List<ZiIstoric>>(){}.getType();
        return gson.fromJson(json, type);
    }

    public void salveazaIstoric(List<ZiIstoric> istoric){
        String json = gson.toJson(istoric);
        prefs.edit().putString(KEY_ISTORIC, json).apply();
    }

    public void adaugaZiInIstoric(ZiIstoric zi){
        List<ZiIstoric> istoric = getIstoric();
        istoric.add(0, zi); // se adauga la inceputul listei cea mai recenta zi
        salveazaIstoric(istoric);
    }

    // Reseteaza goal-ul la 12 noaptea
    public void verificaNouaZi(){
        java.time.LocalDate azi = java.time.LocalDate.now();
        String dataAzi = azi.toString();
        String dataZiPrecedenta = getZiPrecedenta();

        if(dataZiPrecedenta.isEmpty()){
            setZiPrecedenta(dataAzi);
            return;
        }

        if (dataZiPrecedenta.equals(dataAzi)){
            return;
        }

        reseteazaZi(getMlBautiAzi(), dataZiPrecedenta);
        reseteazaMlBautiAzi();
        setZiPrecedenta(dataAzi);
    }

    private void reseteazaZi(int mlBauti, String dataZiPrecedenta){
        if (mlBauti>0){
            java.time.LocalDate dataVeche = java.time.LocalDate.parse(dataZiPrecedenta);
            String dataFormatata = formateazaData(dataVeche);

            ZiIstoric zi = new ZiIstoric(dataZiPrecedenta, dataFormatata, mlBauti, getGoal());
            adaugaZiInIstoric(zi);
        }
    }

    private static String formateazaData(java.time.LocalDate dataNonFormatata){
        int zi = dataNonFormatata.getDayOfMonth();
        String sufixData;
        if (zi >= 11 && zi <= 13){
            sufixData = "th";
        }else {
            switch (zi % 10){
                case 1:
                    sufixData = "st";
                    break;
                case 2:
                    sufixData = "nd";
                    break;
                case 3:
                    sufixData = "rd";
                    break;
                default:
                    sufixData = "th";
                    break;
            }
        }

        String luna = dataNonFormatata.format(java.time.format.DateTimeFormatter.ofPattern("MMMM"));

        return luna + " " + zi + sufixData + " " + dataNonFormatata.getYear();
    }

}
