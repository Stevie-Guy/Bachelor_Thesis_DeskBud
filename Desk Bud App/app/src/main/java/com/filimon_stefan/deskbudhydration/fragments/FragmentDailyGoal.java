package com.filimon_stefan.deskbudhydration.fragments;

import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.fragment.app.Fragment;

import com.filimon_stefan.deskbudhydration.preparation.PrefsHelper;
import com.filimon_stefan.deskbudhydration.R;
import com.google.android.material.card.MaterialCardView;
import com.google.android.material.textfield.TextInputEditText;


public class FragmentDailyGoal extends Fragment {

    private TextView tvWarningSetGoal;
    private MaterialCardView cardGoal;
    private TextView tvCantitateConsumata;
    private TextView tvUnitateMasuraMl;
    private TextView tvGoal;
    private TextView tvProcentGoal;
    private ProgressBar progressGoal;
    private TextInputEditText tietAdaugaApaCustom;
    private Button btnAdaugaCustom;
    private Button btn100ml;
    private Button btn250ml;
    private Button btn500ml;
    private Button btn1000ml;
    private TextInputEditText tietStergeApa;
    private Button btnSterge;

    private PrefsHelper prefs;

    @Nullable
    @Override
    public View onCreateView(@NonNull LayoutInflater inflater,
                             @Nullable ViewGroup container,
                             @Nullable Bundle savedInstanceState){
        return inflater.inflate(R.layout.fragment_daily_goal, container, false);
    }

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState){
        super.onViewCreated(view,savedInstanceState);

        this.prefs = new PrefsHelper(requireContext());

        tvWarningSetGoal = view.findViewById(R.id.tv_warning_goal_not_set);

        cardGoal = view.findViewById(R.id.card_view_goal);
        tvCantitateConsumata = view.findViewById(R.id.tv_cantitate_consumata);
        tvUnitateMasuraMl = view.findViewById(R.id.tv_unitate_masura_cant_consumata);
        tvGoal = view.findViewById(R.id.tv_goal);
        tvProcentGoal = view.findViewById(R.id.tv_procent_din_goal);
        progressGoal = view.findViewById(R.id.progress_goal);

        tietAdaugaApaCustom = view.findViewById(R.id.tiet_adaugare_apa_custom);
        btnAdaugaCustom = view.findViewById(R.id.btn_adauga);

        btn100ml = view.findViewById(R.id.btn_100ml);
        btn250ml = view.findViewById(R.id.btn_250ml);
        btn500ml = view.findViewById(R.id.btn_500ml);
        btn1000ml = view.findViewById(R.id.btn_1000ml);

        tietStergeApa = view.findViewById(R.id.tiet_sterge_apa_bauta);
        btnSterge = view.findViewById(R.id.btn_sterge);

        btn100ml.setOnClickListener(v -> adaugaApa(100));
        btn250ml.setOnClickListener(v -> adaugaApa(250));
        btn500ml.setOnClickListener(v -> adaugaApa(500));
        btn1000ml.setOnClickListener(v -> adaugaApa(1000));

        btnAdaugaCustom.setOnClickListener(v -> adaugaApaCustom());
        btnSterge.setOnClickListener(v -> introduApaDeSters());
    }

    @Override
    public void onResume(){
        super.onResume();
        prefs.verificaNouaZi();
        // Actualizam UI atunci cand userul schimba de la un tab la altul
        refreshUI();
    }

    private void refreshUI(){
        if (prefs.aFolositCalculator()){
            tvWarningSetGoal.setVisibility(View.GONE);
        }else{
            tvWarningSetGoal.setVisibility(View.VISIBLE);
        }

        int mlAzi = prefs.getMlBautiAzi();
        int goal = prefs.getGoal();

        if (mlAzi > goal){
            tvCantitateConsumata.setTextColor(getResources().getColor(R.color.text_procent_goal_atins, null));
            tvUnitateMasuraMl.setTextColor(getResources().getColor(R.color.text_procent_goal_atins, null));
            cardGoal.setCardBackgroundColor(getResources().getColor(R.color.background_card_goal_atins,null));
            cardGoal.setStrokeColor(getResources().getColor(R.color.stroke_card_goal_atins, null));
        }else{
            tvCantitateConsumata.setTextColor(getResources().getColor(R.color.text_procent_goal_neatins, null));
            tvUnitateMasuraMl.setTextColor(getResources().getColor(R.color.text_procent_goal_neatins, null));
            cardGoal.setCardBackgroundColor(getResources().getColor(R.color.background_card_goal_neatins,null));
            cardGoal.setStrokeColor(getResources().getColor(R.color.stroke_card_goal_neatins, null));
        }
        tvCantitateConsumata.setText(String.valueOf(mlAzi));

        float litri = goal / 1000f;
        String goalText = "Goal: " + goal + " ml (" + String.format("%.1f", litri) + "L)";

        tvGoal.setText(goalText);

        int procentGoal;
        if (goal > 0){
            procentGoal = Math.round((mlAzi * 100f) / goal);
        }else {
            procentGoal = 0;
        }
        tvProcentGoal.setText(procentGoal + "% din total");

        procentGoal = Math.min(procentGoal, 100);
        if (procentGoal == 100){
            progressGoal.setProgressDrawable(
                    androidx.core.content.ContextCompat.getDrawable(
                            requireContext(), R.drawable.progress_bar_goal_atins
                    )
            );
        }else{
            progressGoal.setProgressDrawable(
                    androidx.core.content.ContextCompat.getDrawable(
                            requireContext(), R.drawable.progress_bar_gradient
                    )
            );
        }
        progressGoal.setProgress(procentGoal);
    }

    private void adaugaApa(int ml){
        prefs.adaugaMlBauti(ml);
        refreshUI();
    }

    private void scadeApa(int ml){
        prefs.scadeMlBauti(ml);
        refreshUI();
    }

    private void adaugaApaCustom(){
        String textCantitateApa;
        if (tietAdaugaApaCustom.getText() != null){
            textCantitateApa = tietAdaugaApaCustom.getText().toString().trim();
        }else{
            textCantitateApa = "";
        }

        if (textCantitateApa.isEmpty()){
            Toast.makeText(requireContext(),"Introduceți cantitatea băută astăzi.", Toast.LENGTH_SHORT).show();
            return;
        }

        int ml;
        try {
            ml = Integer.parseInt(textCantitateApa);
        }catch (NumberFormatException e){
            Toast.makeText(requireContext(), "Cantitate invalidă!", Toast.LENGTH_SHORT).show();
            return;
        }

        if (ml <= 0) {
            Toast.makeText(requireContext(),"Cantitatea trebuie să fie pozitivă.", Toast.LENGTH_SHORT).show();
            return;
        }

        adaugaApa(ml);
        tietAdaugaApaCustom.setText("");
    }

    private void introduApaDeSters(){
        String textCantitateApaDeSters;
        if (tietStergeApa.getText() != null){
            textCantitateApaDeSters = tietStergeApa.getText().toString().trim();
        }else {
            textCantitateApaDeSters = "";
        }

        if (textCantitateApaDeSters.isEmpty()){
            Toast.makeText(requireContext(), "Introduceti cantitate validă de sters.", Toast.LENGTH_SHORT).show();
            return;
        }

        int mlSterge;
        try {
            mlSterge = Integer.parseInt(textCantitateApaDeSters);
        }catch (NumberFormatException e){
            Toast.makeText(requireContext(), "Cantitate invalidă!", Toast.LENGTH_SHORT).show();
            return;
        }

        if (mlSterge <= 0) {
            Toast.makeText(requireContext(),"Cantitatea trebuie să fie pozitivă.", Toast.LENGTH_SHORT).show();
            return;
        }

        scadeApa(mlSterge);
        tietStergeApa.setText("");
    }
}
