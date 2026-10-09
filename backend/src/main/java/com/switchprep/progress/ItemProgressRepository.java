package com.switchprep.progress;

import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

public interface ItemProgressRepository extends JpaRepository<ItemProgress, Long> {

    List<ItemProgress> findByUserId(Long userId);

    Optional<ItemProgress> findByUserIdAndItemKey(Long userId, String itemKey);

    void deleteByUserIdAndItemKey(Long userId, String itemKey);

    void deleteByUserId(Long userId);

    @Query("select p.section, count(p) from ItemProgress p where p.userId = ?1 and p.done = true group by p.section")
    List<Object[]> countDoneBySection(Long userId);
}
