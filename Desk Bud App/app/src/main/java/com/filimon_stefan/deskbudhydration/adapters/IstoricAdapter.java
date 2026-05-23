package com.filimon_stefan.deskbudhydration.adapters;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;

import com.filimon_stefan.deskbudhydration.R;
import com.filimon_stefan.deskbudhydration.preparation.ZiIstoric;

import java.util.List;

public class IstoricAdapter extends RecyclerView.Adapter<IstoricAdapter.IstoricViewHolder> {
    private final List<ZiIstoric> listaIstoric;

    public IstoricAdapter(List<ZiIstoric> listaIstoric) {
        this.listaIstoric = listaIstoric;
    }

    // Clasa interna care reprezinta un o zi din istoric
    public static class IstoricViewHolder extends RecyclerView.ViewHolder{
        TextView tvData;
        TextView tvMl;
        TextView tvProcent;

        public IstoricViewHolder(@NonNull View itemView){
            super(itemView);
            tvData = itemView.findViewById(R.id.tv_data_istoric);
            tvMl = itemView.findViewById(R.id.tv_ml_istoric);
            tvProcent = itemView.findViewById(R.id.tv_procent_istoric);
        }
    }

    @NonNull
    @Override
    public IstoricViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType){
        View view = LayoutInflater.from(parent.getContext())
                .inflate(R.layout.item_istoric, parent, false);
        return new IstoricViewHolder(view);
    }

    @Override
    public void onBindViewHolder(@NonNull IstoricViewHolder holder, int position){
        ZiIstoric zi = listaIstoric.get(position);

        holder.tvData.setText(zi.getDataFormatata());
        holder.tvMl.setText(zi.getMlBauti() + " ml");
        holder.tvProcent.setText(zi.getProcent() + "%");

        if(zi.esteGoalulZileiAtins()){
            holder.tvProcent.setBackgroundResource(R.drawable.istoric_procent_atins);
            holder.tvProcent.setTextColor(holder.itemView.getContext().getColor(R.color.text_procent_goal_atins));
        }else{
            holder.tvProcent.setBackgroundResource(R.drawable.istoric_procent_neatins);
            holder.tvProcent.setTextColor(holder.itemView.getContext().getColor(R.color.text_procent_goal_neatins));
        }
    }

    @Override
    public int getItemCount(){
        return listaIstoric.size();
    }
}
