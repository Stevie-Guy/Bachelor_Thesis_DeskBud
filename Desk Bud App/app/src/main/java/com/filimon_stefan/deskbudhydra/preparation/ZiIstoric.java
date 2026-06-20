package com.filimon_stefan.deskbudhydra.preparation;

public class ZiIstoric {
    private String data; // format: YYYY-MM-DD
    private String dataFormatata; // format afisat in istoric(May 5th 2026)
    private int mlBauti;
    private int goalulZileiDinIstoric;

    public ZiIstoric(String data, String dataFormatata, int mlBauti, int goalulZileiDinIstoric) {
        this.data = data;
        this.dataFormatata = dataFormatata;
        this.mlBauti = mlBauti;
        this.goalulZileiDinIstoric = goalulZileiDinIstoric;
    }

    public String getData() {
        return data;
    }

    public String getDataFormatata() {
        return dataFormatata;
    }

    public int getMlBauti() {
        return mlBauti;
    }

    public int getGoalulZileiDinIstoric() {
        return goalulZileiDinIstoric;
    }

    // Se calculeaza procentul pentru ziua respectiva
    public int getProcent(){
        if(goalulZileiDinIstoric == 0) return 0;
        return (int) Math.round((this.mlBauti * 100.0) / this.goalulZileiDinIstoric);
    }

    // Functie care verifica daca procentul e >= 100% pentru a face textul verde
    public boolean esteGoalulZileiAtins(){
        if (getProcent() >= 100){
            return true;
        }else{
            return false;
        }
    }
}
